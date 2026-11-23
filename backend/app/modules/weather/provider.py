import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from uuid import uuid4

import httpx

from app.modules.weather.exceptions import (
    WeatherUpstreamRateLimitedError,
    WeatherUpstreamUnavailableError,
)

logger = logging.getLogger("farmmate")


class WeatherProvider:

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

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

    _TRANSPORT_ERRORS = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.TransportError,
    )

    def __init__(
        self,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        # Injectable transport for tests (httpx.MockTransport);
        # the production client still uses the default connection pool.
        self._transport = transport

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:

        # Correlation id for request tracing in logs. It is logged
        # alongside provider status, but never alongside coordinates
        # or any credential.
        correlation_id = uuid4().hex[:8]

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "weather_code,"
                "wind_speed_10m,"
                "surface_pressure,"
                "precipitation,"
                "is_day"
            ),
            "daily": (
                "sunrise,"
                "sunset,"
                "precipitation_probability_max,"
                "uv_index_max"
            ),
            "timezone": "auto",
        }

        async with httpx.AsyncClient(
            timeout=10,
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

                return response.json()

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
