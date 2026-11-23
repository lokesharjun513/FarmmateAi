from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.weather.cache import (
    WeatherCache,
    build_weather_cache_key,
    default_weather_cache,
)
from app.modules.weather.provider import (
    WEATHERAPI_TO_WMO,
    WeatherProvider,
)
from app.modules.weather.location_provider import LocationProvider
from app.modules.weather.schemas import (
    CurrentWeatherResponse,
    WeatherRecommendationResponse,
)


@dataclass(frozen=True)
class WeatherResult:
    """
    Result of a current-weather lookup.

    ``stale`` is True when the response was rebuilt from the last
    successful observation because the upstream fetch failed.
    """

    data: CurrentWeatherResponse
    stale: bool = False


class WeatherService:

    def __init__(
        self,
        weather_provider: WeatherProvider | None = None,
        location_provider: LocationProvider | None = None,
        cache: WeatherCache | None = None,
    ):
        self.weather_provider = (
            weather_provider or WeatherProvider()
        )

        self.location_provider = (
            location_provider or LocationProvider()
        )

        # Shared across all WeatherService instances (services are
        # created per request), so cached weather survives requests.
        self.cache = cache or default_weather_cache

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        location: str | None = None,
    ) -> WeatherResult:

        key = build_weather_cache_key(latitude, longitude)

        result = await self.cache.get_or_fetch(
            key,
            lambda: self._fetch_and_build(
                latitude=latitude,
                longitude=longitude,
                location=location,
            ),
        )

        return WeatherResult(
            data=result.data,
            stale=result.stale,
        )

    async def _fetch_and_build(
        self,
        *,
        latitude: float,
        longitude: float,
        location: str | None,
    ) -> CurrentWeatherResponse:

        # ------------------------------------------------------
        # 1. Resolve actual location
        # ------------------------------------------------------

        resolved_location = await self.location_provider.get_location_name(
            latitude=latitude,
            longitude=longitude,
        )

        # ------------------------------------------------------
        # 2. Get weather
        # ------------------------------------------------------

        weather_data = await self.weather_provider.get_current_weather(
            latitude=latitude,
            longitude=longitude,
        )

        current = weather_data.get("current", {})
        condition = current.get("condition") or {}

        forecast = weather_data.get("forecast", {})
        forecastday = forecast.get("forecastday") or []
        first_day = forecastday[0] if forecastday else {}
        day = first_day.get("day") or {}
        astro = first_day.get("astro") or {}
        api_location = weather_data.get("location") or {}

        # ------------------------------------------------------
        # 3. Location
        # ------------------------------------------------------

        # Preserve the existing location-name behavior (reverse
        # geocoding via Nominatim). Only when that lookup degraded
        # to the "Current Location" placeholder do we use the
        # provider's own place name instead.
        if resolved_location == "Current Location":
            api_name = api_location.get("name")

            if isinstance(api_name, str) and api_name.strip():
                resolved_location = api_name.strip()

        # ------------------------------------------------------
        # 4. Current conditions (units match the existing contract:
        #    C, C, %, km/h, hPa, km, uv index, mm)
        # ------------------------------------------------------

        temperature = float(current["temp_c"])
        wind_speed = float(current["wind_kph"])

        api_code = condition.get("code")
        weather_code = int(
            WEATHERAPI_TO_WMO.get(api_code, api_code)
        )

        weather_condition = condition["text"].strip()

        # ------------------------------------------------------
        # 5. Sunrise / sunset (timezone-aware ISO 8601)
        # ------------------------------------------------------

        # WeatherAPI returns astro times as "hh:mm AM/PM" strings in
        # the location's timezone (location.tz_id, IANA). Combine with
        # the forecast date to build an aware datetime; if any piece
        # is missing or unparseable, serve None rather than guessing.
        sunrise = self._parse_astro_time(
            first_day.get("date"),
            astro.get("sunrise"),
            api_location.get("tz_id"),
        )

        sunset = self._parse_astro_time(
            first_day.get("date"),
            astro.get("sunset"),
            api_location.get("tz_id"),
        )

        # ------------------------------------------------------
        # 6. Return response
        # ------------------------------------------------------

        return CurrentWeatherResponse(
            location=resolved_location,
            latitude=latitude,
            longitude=longitude,
            temperature=temperature,
            feels_like=self._opt_float(current.get("feelslike_c")),
            humidity=self._opt_int(current.get("humidity")),
            wind_speed=wind_speed,
            pressure=self._opt_float(current.get("pressure_mb")),
            visibility=self._opt_float(current.get("vis_km")),
            uv_index=self._opt_float(current.get("uv")),
            precipitation=self._opt_float(current.get("precip_mm")),
            weather_code=weather_code,
            weather_condition=weather_condition,
            rain_probability=self._opt_int(
                day.get("daily_chance_of_rain")
            ),
            sunrise=sunrise,
            sunset=sunset,
        )

    @staticmethod
    def _opt_float(value) -> float | None:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return None

    @staticmethod
    def _opt_int(value) -> int | None:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(round(float(value)))
        return None

    @staticmethod
    def _parse_astro_time(
        date_str: str | None,
        time_str: str | None,
        tz_id: str | None,
    ) -> datetime | None:

        if not date_str or not time_str or not tz_id:
            return None

        try:
            date_part = datetime.strptime(
                str(date_str),
                "%Y-%m-%d",
            ).date()

            time_part = datetime.strptime(
                str(time_str).strip(),
                "%I:%M %p",
            ).time()

            tz = ZoneInfo(str(tz_id))
        except (TypeError, ValueError, ZoneInfoNotFoundError):
            return None

        return datetime.combine(date_part, time_part, tzinfo=tz)

    async def get_weather_recommendation(
        self,
        latitude: float,
        longitude: float,
        location: str | None = None,
    ) -> WeatherRecommendationResponse:

        weather = (await self.get_current_weather(
            latitude=latitude,
            longitude=longitude,
            location=location,
        )).data

        # Basic recommendation for now.
        # We can make this AI/farming-specific later.

        if (
            weather.rain_probability is not None
            and weather.rain_probability >= 70
        ):
            return WeatherRecommendationResponse(
                recommendation=(
                    "Rain is likely today. "
                    "Consider avoiding irrigation and "
                    "plan field activities accordingly."
                ),
                priority="high",
            )

        if weather.temperature >= 35:
            return WeatherRecommendationResponse(
                recommendation=(
                    "High temperature expected. "
                    "Check crop moisture and avoid heavy "
                    "field work during peak afternoon heat."
                ),
                priority="medium",
            )

        return WeatherRecommendationResponse(
            recommendation=(
                "Weather conditions look suitable for "
                "normal farm activities today."
            ),
            priority="low",
        )
