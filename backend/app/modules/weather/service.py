from app.modules.weather.provider import WeatherProvider
from app.modules.weather.location_provider import LocationProvider
from app.modules.weather.schemas import (
    CurrentWeatherResponse,
    WeatherRecommendationResponse,
)


class WeatherService:

    def __init__(
        self,
        weather_provider: WeatherProvider | None = None,
        location_provider: LocationProvider | None = None,
    ):
        self.weather_provider = (
            weather_provider or WeatherProvider()
        )

        self.location_provider = (
            location_provider or LocationProvider()
        )

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        location: str | None = None,
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
        daily = weather_data.get("daily", {})

        # ------------------------------------------------------
        # 3. Weather values
        # ------------------------------------------------------

        temperature = float(
            current.get("temperature_2m", 0)
        )

        feels_like = current.get(
            "apparent_temperature"
        )

        humidity = current.get(
            "relative_humidity_2m"
        )

        wind_speed = float(
            current.get("wind_speed_10m", 0)
        )

        pressure = current.get(
            "surface_pressure"
        )

        precipitation = current.get(
            "precipitation"
        )

        weather_code = int(
            current.get("weather_code", 0)
        )

        # ------------------------------------------------------
        # 4. Weather condition
        # ------------------------------------------------------

        weather_condition = self._get_weather_condition(
            weather_code
        )

        # ------------------------------------------------------
        # 5. Rain probability
        # ------------------------------------------------------

        rain_probability = None

        precipitation_probability = daily.get(
            "precipitation_probability_max"
        )

        if (
            isinstance(precipitation_probability, list)
            and precipitation_probability
        ):
            rain_probability = precipitation_probability[0]

        # ------------------------------------------------------
        # 6. Sunrise / sunset
        # ------------------------------------------------------

        sunrise = None
        sunset = None

        sunrise_values = daily.get("sunrise")
        sunset_values = daily.get("sunset")

        if isinstance(sunrise_values, list) and sunrise_values:
            sunrise = sunrise_values[0]

        if isinstance(sunset_values, list) and sunset_values:
            sunset = sunset_values[0]

        # ------------------------------------------------------
        # 7. Return response
        # ------------------------------------------------------

        return CurrentWeatherResponse(
            location=resolved_location,
            latitude=latitude,
            longitude=longitude,
            temperature=temperature,
            feels_like=feels_like,
            humidity=humidity,
            wind_speed=wind_speed,
            pressure=pressure,
            visibility=None,
            uv_index=None,
            precipitation=precipitation,
            weather_code=weather_code,
            weather_condition=weather_condition,
            rain_probability=rain_probability,
            sunrise=sunrise,
            sunset=sunset,
        )

    @staticmethod
    def _get_weather_condition(
        weather_code: int,
    ) -> str:

        weather_conditions = {
            0: "Clear Sky",
            1: "Mainly Clear",
            2: "Partly Cloudy",
            3: "Overcast",

            45: "Fog",
            48: "Depositing Rime Fog",

            51: "Light Drizzle",
            53: "Moderate Drizzle",
            55: "Dense Drizzle",

            56: "Light Freezing Drizzle",
            57: "Dense Freezing Drizzle",

            61: "Slight Rain",
            63: "Moderate Rain",
            65: "Heavy Rain",

            66: "Light Freezing Rain",
            67: "Heavy Freezing Rain",

            71: "Slight Snow",
            73: "Moderate Snow",
            75: "Heavy Snow",

            77: "Snow Grains",

            80: "Slight Rain Showers",
            81: "Moderate Rain Showers",
            82: "Violent Rain Showers",

            85: "Slight Snow Showers",
            86: "Heavy Snow Showers",

            95: "Thunderstorm",
            96: "Thunderstorm with Slight Hail",
            99: "Thunderstorm with Heavy Hail",
        }

        return weather_conditions.get(
            weather_code,
            "Unknown",
        )

    async def get_weather_recommendation(
        self,
        latitude: float,
        longitude: float,
        location: str | None = None,
    ) -> WeatherRecommendationResponse:

        weather = await self.get_current_weather(
            latitude=latitude,
            longitude=longitude,
            location=location,
        )

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