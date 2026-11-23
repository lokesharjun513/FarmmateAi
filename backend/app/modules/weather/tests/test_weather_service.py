from datetime import datetime

import pytest

from app.modules.weather.cache import WeatherCache
from app.modules.weather.service import WeatherService
from app.modules.weather.schemas import (
    CurrentWeatherResponse,
    WeatherRecommendationResponse,
)


class MockWeatherProvider:

    def __init__(self, data):
        self.data = data
        self.called_with = None

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ):
        self.called_with = (latitude, longitude)
        return self.data


class MockLocationProvider:

    def __init__(
        self,
        location="Nellore, Andhra Pradesh",
    ):
        self.location = location
        self.called_with = None

    async def get_location_name(
        self,
        latitude: float,
        longitude: float,
    ):
        self.called_with = (latitude, longitude)
        return self.location


# ============================================================
# get_current_weather()
# ============================================================


@pytest.mark.asyncio
async def test_get_current_weather_success():

    weather_data = {
        "current": {
            "temperature_2m": 32.5,
            "relative_humidity_2m": 70,
            "apparent_temperature": 35.0,
            "weather_code": 0,
            "wind_speed_10m": 12.0,
            "surface_pressure": 1008.0,
            "precipitation": 0.0,
        },
        "daily": {
            "precipitation_probability_max": [20],
            "sunrise": ["2026-08-15T05:45"],
            "sunset": ["2026-08-15T18:30"],
        },
    }

    weather_provider = MockWeatherProvider(
        weather_data
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.4426,
        longitude=79.9865,
    )).data

    assert isinstance(
        result,
        CurrentWeatherResponse,
    )

    assert result.location == (
        "Nellore, Andhra Pradesh"
    )

    assert result.latitude == 14.4426
    assert result.longitude == 79.9865

    assert result.temperature == 32.5
    assert result.feels_like == 35.0
    assert result.humidity == 70

    assert result.wind_speed == 12.0
    assert result.pressure == 1008.0
    assert result.precipitation == 0.0

    assert result.weather_code == 0
    assert result.weather_condition == "Clear Sky"

    assert result.rain_probability == 20

    assert result.sunrise == datetime(
        2026,
        8,
        15,
        5,
        45,
    )

    assert result.sunset == datetime(
        2026,
        8,
        15,
        18,
        30,
    )


@pytest.mark.asyncio
async def test_get_current_weather_calls_providers_with_coordinates():

    weather_provider = MockWeatherProvider(
        {
            "current": {},
            "daily": {},
        }
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    await service.get_current_weather(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert weather_provider.called_with == (
        14.4426,
        79.9865,
    )

    assert location_provider.called_with == (
        14.4426,
        79.9865,
    )


@pytest.mark.asyncio
async def test_get_current_weather_handles_missing_current_data():

    weather_provider = MockWeatherProvider(
        {
            "daily": {},
        }
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.0,
        longitude=79.0,
    )).data

    assert result.temperature == 0
    assert result.wind_speed == 0
    assert result.weather_code == 0

    assert result.rain_probability is None
    assert result.sunrise is None
    assert result.sunset is None


@pytest.mark.asyncio
async def test_get_current_weather_handles_empty_daily_data():

    weather_provider = MockWeatherProvider(
        {
            "current": {
                "temperature_2m": 30,
                "wind_speed_10m": 10,
                "weather_code": 0,
            },
            "daily": {},
        }
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.0,
        longitude=79.0,
    )).data

    assert result.rain_probability is None
    assert result.sunrise is None
    assert result.sunset is None


@pytest.mark.asyncio
async def test_get_current_weather_handles_empty_daily_lists():

    weather_provider = MockWeatherProvider(
        {
            "current": {
                "temperature_2m": 30,
                "wind_speed_10m": 10,
                "weather_code": 0,
            },
            "daily": {
                "precipitation_probability_max": [],
                "sunrise": [],
                "sunset": [],
            },
        }
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.0,
        longitude=79.0,
    )).data

    assert result.rain_probability is None
    assert result.sunrise is None
    assert result.sunset is None


# ============================================================
# _get_weather_condition()
# ============================================================


@pytest.mark.parametrize(
    "weather_code,expected",
    [
        (0, "Clear Sky"),
        (1, "Mainly Clear"),
        (2, "Partly Cloudy"),
        (3, "Overcast"),
        (45, "Fog"),
        (61, "Slight Rain"),
        (63, "Moderate Rain"),
        (65, "Heavy Rain"),
        (95, "Thunderstorm"),
        (
            96,
            "Thunderstorm with Slight Hail",
        ),
        (
            99,
            "Thunderstorm with Heavy Hail",
        ),
    ],
)
def test_get_weather_condition(
    weather_code,
    expected,
):

    result = WeatherService._get_weather_condition(
        weather_code
    )

    assert result == expected


def test_get_weather_condition_unknown():

    result = WeatherService._get_weather_condition(
        999
    )

    assert result == "Unknown"


# ============================================================
# get_weather_recommendation()
# ============================================================


@pytest.mark.asyncio
async def test_get_weather_recommendation_heavy_rain():

    weather_provider = MockWeatherProvider(
        {
            "current": {
                "temperature_2m": 30,
                "wind_speed_10m": 10,
                "weather_code": 61,
            },
            "daily": {
                "precipitation_probability_max": [80],
            },
        }
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = await service.get_weather_recommendation(
        latitude=14.0,
        longitude=79.0,
    )

    assert isinstance(
        result,
        WeatherRecommendationResponse,
    )

    assert result.priority == "high"

    assert (
        "Rain is likely"
        in result.recommendation
    )


@pytest.mark.asyncio
async def test_get_weather_recommendation_high_temperature():

    weather_provider = MockWeatherProvider(
        {
            "current": {
                "temperature_2m": 38,
                "wind_speed_10m": 10,
                "weather_code": 0,
            },
            "daily": {
                "precipitation_probability_max": [10],
            },
        }
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = await service.get_weather_recommendation(
        latitude=14.0,
        longitude=79.0,
    )

    assert result.priority == "medium"

    assert (
        "High temperature"
        in result.recommendation
    )


@pytest.mark.asyncio
async def test_get_weather_recommendation_normal_weather():

    weather_provider = MockWeatherProvider(
        {
            "current": {
                "temperature_2m": 30,
                "wind_speed_10m": 10,
                "weather_code": 0,
            },
            "daily": {
                "precipitation_probability_max": [10],
            },
        }
    )

    location_provider = MockLocationProvider()

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = await service.get_weather_recommendation(
        latitude=14.0,
        longitude=79.0,
    )

    assert result.priority == "low"

    assert (
        "suitable"
        in result.recommendation
    )