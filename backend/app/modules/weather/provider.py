"""WeatherAPI.com provider for FarmMate weather data.

Primary provider (https://www.weatherapi.com/, forecast API). The
legacy Open-Meteo provider is preserved for rollback in
``provider_openmeteo.py`` and is never invoked automatically.
"""

import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from uuid import uuid4

import httpx

from app.core.config import settings
from app.modules.weather.exceptions import (
    WeatherUpstreamRateLimitedError,
    WeatherUpstreamUnavailableError,
)

logger = logging.getLogger("farmmate")


# WeatherAPI.com condition codes are not WMO codes. The contract for
# FarmMate weather responses uses WMO weather codes (see
# weather/constants.py), so each WeatherAPI code is mapped to the WMO
# category closest to its description. Unknown codes pass through
# unchanged; no data is ever invented.
WEATHERAPI_TO_WMO: dict[int, int] = {
    1000: 0,   # Clear -> Clear Sky
    1003: 2,   # Partly cloudy -> Partly Cloudy
    1006: 3,   # Cloudy -> Overcast
    1009: 3,   # Overcast -> Overcast
    1030: 45,  # Mist -> Fog
    1063: 61,  # Patchy rain possible -> Slight Rain
    1066: 71,  # Patchy snow possible -> Slight Snow
    1069: 66,  # Patchy sleet possible -> Light Freezing Rain
    1072: 56,  # Patchy freezing drizzle possible -> Light Freezing Drizzle
    1087: 95,  # Thundery outbreaks possible -> Thunderstorm
    1114: 75,  # Blowing snow -> Heavy Snow
    1117: 75,  # Blizzard -> Heavy Snow
    1135: 45,  # Fog -> Fog
    1147: 48,  # Freezing fog -> Depositing Rime Fog
    1150: 51,  # Patchy light drizzle -> Light Drizzle
    1153: 53,  # Light drizzle -> Moderate Drizzle
    1168: 56,  # Freezing drizzle -> Light Freezing Drizzle
    1171: 57,  # Heavy freezing drizzle -> Dense Freezing Drizzle
    1180: 61,  # Patchy light rain -> Slight Rain
    1183: 61,  # Light rain -> Slight Rain
    1186: 63,  # Moderate rain at times -> Moderate Rain
    1189: 63,  # Moderate rain -> Moderate Rain
    1192: 65,  # Heavy rain at times -> Heavy Rain
    1195: 65,  # Heavy rain -> Heavy Rain
    1198: 66,  # Light freezing rain -> Light Freezing Rain
    1201: 67,  # Moderate or heavy freezing rain -> Heavy Freezing Rain
    1204: 66,  # Light sleet -> Light Freezing Rain
    1207: 67,  # Moderate or heavy sleet -> Heavy Freezing Rain
    1210: 71,  # Patchy light snow -> Slight Snow
    1213: 71,  # Light snow -> Slight Snow
    1216: 73,  # Patchy moderate snow -> Moderate Snow
    1219: 73,  # Moderate snow -> Moderate Snow
    1222: 75,  # Patchy heavy snow -> Heavy Snow
    1225: 75,  # Heavy snow -> Heavy Snow
    1237: 79,  # Ice pellets -> Ice Pellets (WMO 79)
    1240: 80,  # Light rain shower -> Slight Rain Showers
    1243: 81,  # Moderate or heavy rain shower -> Moderate Rain Showers
    1246: 82,  # Torrential rain shower -> Violent Rain Showers
    1249: 85,  # Light sleet showers -> Slight Snow Showers
    1252: 86,  # Moderate or heavy sleet showers -> Heavy Snow Showers
    1255: 85,  # Light snow showers -> Slight Snow Showers
    1258: 86,  # Moderate or heavy snow showers -> Heavy Snow Showers
    1261: 79,  # Light showers of ice pellets -> Ice Pellets
    1264: 79,  # Moderate or heavy showers of ice pellets -> Ice Pellets
    1273: 95,  # Patchy light rain with thunder -> Thunderstorm
    1276: 95,  # Moderate or heavy rain with thunder -> Thunderstorm
    1279: 95,  # Patchy light snow with thunder -> Thunderstorm
    1282: 95,  # Moderate or heavy snow with thunder -> Thunderstorm
}


class WeatherProvider:

    BASE_URL = "https://api.weatherapi.com/v1/forecast.json"

    # First attempt + a single bounded retry. We deliberately do
    # not retry more than once per request: with a 15-minute cache
    # in front of the provider, a failed request will be retried
    # on a later (cached) call rather than hammering the upstream.
    MAX_TOTAL_ATTEMPTS = 2

    # Backoff when the upstream does not tell us how long to wait.
    DEFAULT_BACKOFF_SECONDS = 1.0

    # Upper bound for any retry wait (from Retry-After or backoff),
    # so a single request can never stall for a very long time.
    MAX_RETRY_WAIT_SECONDS = 10.0

    REQUEST_TIMEOUT_SECONDS = 10.0

    _TRANSPORT_ERRORS = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.TransportError,
    )

    def __init__(
        self,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        api_key: str | None = None,
    ):
        # Injectable transport for tests (httpx.MockTransport);
        # the production client still uses the default connection pool.
        self._transport = transport

        # Injectable API key for tests; in production the key is read
        # from the WEATHERAPI_API_KEY environment variable (never
        # stored in code and never logged).
        self._api_key = api_key

    @property
    def _resolved_api_key(self) -> str | None:
        if self._api_key is not None:
            return self._api_key
        secret = settings.WEATHERAPI_API_KEY
        return secret.get_secret_value() if secret else None

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:

        # Correlation id for request tracing in logs. It is logged
        # alongside provider status, but never alongside coordinates
        # or any credential.
        correlation_id = uuid4().hex[:8]

        api_key = self._resolved_api_key

        if not api_key:
            logger.error(
                "weather provider API key is not configured "
                "[correlation=%s]",
                correlation_id,
            )
            raise WeatherUpstreamUnavailableError(
                "Weather provider is not configured."
            )

        params = {
            "key": api_key,
            "q": f"{latitude},{longitude}",
            "days": 1,
            "aqi": "no",
            "alerts": "no",
        }

        data = await self._request(params, correlation_id)

        self._validate_response(data)

        return data

    async def _request(
        self,
        params: dict,
        correlation_id: str,
    ) -> dict:

        async with httpx.AsyncClient(
            timeout=self.REQUEST_TIMEOUT_SECONDS,
            transport=self._transport,
        ) as client:

            attempt = 1

            while True:

                try:

                    response = await client.get(
                        self.BASE_URL,
                        params=params,
                    )

                except self._TRANSPORT_ERRORS as exc:

                    if attempt >= self.MAX_TOTAL_ATTEMPTS:
                        logger.warning(
                            "weather provider request failed [correlation=%s] "
                            "attempt=%s/%s error=%s",
                            correlation_id,
                            attempt,
                            self.MAX_TOTAL_ATTEMPTS,
                            type(exc).__name__,
                        )
                        raise WeatherUpstreamUnavailableError(
                            "Weather provider is unreachable."
                        ) from exc

                    wait = self._retry_wait(None)
                    logger.warning(
                        "weather provider transport error [correlation=%s] "
                        "attempt=%s/%s retrying_in=%ss error=%s",
                        correlation_id,
                        attempt,
                        self.MAX_TOTAL_ATTEMPTS,
                        wait,
                        type(exc).__name__,
                    )
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue

                if response.status_code in (401, 403):
                    # Rejected/invalid API key: not transient, never
                    # retried. The key itself is never logged.
                    logger.warning(
                        "weather provider auth rejected [correlation=%s] "
                        "status=%s",
                        correlation_id,
                        response.status_code,
                    )
                    raise WeatherUpstreamUnavailableError(
                        "Weather provider rejected the request."
                    )

                if response.status_code == 429:

                    if attempt >= self.MAX_TOTAL_ATTEMPTS:
                        logger.warning(
                            "weather provider rate limited [correlation=%s] "
                            "attempt=%s/%s status=429",
                            correlation_id,
                            attempt,
                            self.MAX_TOTAL_ATTEMPTS,
                        )
                        raise WeatherUpstreamRateLimitedError(
                            "Weather provider is rate limited."
                        )

                    wait = self._retry_wait(response)
                    logger.warning(
                        "weather provider rate limited [correlation=%s] "
                        "attempt=%s/%s retrying_in=%ss status=429",
                        correlation_id,
                        attempt,
                        self.MAX_TOTAL_ATTEMPTS,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue

                if response.status_code >= 500:

                    if attempt >= self.MAX_TOTAL_ATTEMPTS:
                        logger.warning(
                            "weather provider upstream error [correlation=%s] "
                            "attempt=%s/%s status=%s",
                            correlation_id,
                            attempt,
                            self.MAX_TOTAL_ATTEMPTS,
                            response.status_code,
                        )
                        raise WeatherUpstreamUnavailableError(
                            "Weather provider returned a server error."
                        )

                    wait = self._retry_wait(response)
                    logger.warning(
                        "weather provider upstream error [correlation=%s] "
                        "attempt=%s/%s retrying_in=%ss status=%s",
                        correlation_id,
                        attempt,
                        self.MAX_TOTAL_ATTEMPTS,
                        wait,
                        response.status_code,
                    )
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue

                # Other 4xx responses (e.g. 400 bad params) are not
                # transient; do not retry them.
                if response.status_code >= 400:
                    logger.warning(
                        "weather provider request rejected [correlation=%s] "
                        "status=%s",
                        correlation_id,
                        response.status_code,
                    )
                    raise WeatherUpstreamUnavailableError(
                        "Weather provider rejected the request."
                    )

                logger.info(
                    "weather provider ok [correlation=%s] "
                    "attempt=%s status=%s",
                    correlation_id,
                    attempt,
                    response.status_code,
                )

                try:
                    return response.json()
                except ValueError:
                    logger.warning(
                        "weather provider returned malformed json "
                        "[correlation=%s]",
                        correlation_id,
                    )
                    raise WeatherUpstreamUnavailableError(
                        "Weather provider returned an invalid response."
                    )

    @staticmethod
    def _validate_response(data) -> None:
        """Basic structural validation of the WeatherAPI payload.

        Required fields (temperature, wind speed, condition code/text,
        forecast breakdown) must be present and well-typed; anything
        else is treated as an unavailable provider rather than being
        silently filled in with zeroes or invented data. Optional
        measurements are validated downstream in the service.
        """

        if not isinstance(data, dict):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        current = data.get("current")

        if not isinstance(current, dict):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        if not WeatherProvider._is_number(current.get("temp_c")):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        if not WeatherProvider._is_number(current.get("wind_kph")):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        condition = current.get("condition")

        if not isinstance(condition, dict):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        if not WeatherProvider._is_number(condition.get("code")):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        text = condition.get("text")

        if not isinstance(text, str) or not text.strip():
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        forecast = data.get("forecast")

        if not isinstance(forecast, dict):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

        forecastday = forecast.get("forecastday")

        if (
            not isinstance(forecastday, list)
            or not forecastday
            or not isinstance(forecastday[0], dict)
        ):
            raise WeatherUpstreamUnavailableError(
                "Weather provider returned an invalid response."
            )

    @staticmethod
    def _is_number(value) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    def _retry_wait(
        self,
        response: httpx.Response | None,
    ) -> float:

        if response is not None:
            retry_after = response.headers.get("Retry-After")

            if retry_after is not None:
                wait = self._parse_retry_after(retry_after)

                if wait is not None:
                    return max(0.0, min(wait, self.MAX_RETRY_WAIT_SECONDS))

        return self.DEFAULT_BACKOFF_SECONDS

    @staticmethod
    def _parse_retry_after(
        value: str,
    ) -> float | None:

        # RFC 9110 allows either a delay in seconds or an HTTP-date.
        try:
            return float(value)
        except ValueError:
            pass

        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return (parsed - datetime.now(timezone.utc)).total_seconds()
