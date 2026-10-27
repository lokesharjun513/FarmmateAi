import httpx


class WeatherProvider:

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:

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

        try:
            async with httpx.AsyncClient(
                timeout=10,
            ) as client:

                response = await client.get(
                    self.BASE_URL,
                    params=params,
                )

                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as exc:
            raise RuntimeError(
                "Unable to fetch weather."
            ) from exc