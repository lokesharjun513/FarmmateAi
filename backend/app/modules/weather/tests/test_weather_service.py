from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.modules.weather.cache import WeatherCache
from app.modules.weather.provider import WEATHERAPI_TO_WMO
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


def make_payload(**overrides):
    """A complete, valid WeatherAPI.com forecast.json payload."""

    payload = {
        "location": {
            "name": "Nellore",
            "tz_id": "Asia/Kolkata",
        },
        "current": {
            "temp_c": 32.5,
            "feelslike_c": 35.0,
            "humidity": 70,
            "wind_kph": 12.0,
            "pressure_mb": 1008.0,
            "vis_km": 10.0,
            "uv": 8.0,
            "precip_mm": 0.0,
            "condition": {"code": 1000, "text": "Sunny"},
        },
        "forecast": {
            "forecastday": [
                {
                    "date": "2026-11-23",
                    "day": {"daily_chance_of_rain": 20},
                    "astro": {
                        "sunrise": "06:35 AM",
                        "sunset": "05:42 PM",
                    },
                }
            ]
        },
    }

    payload.update(overrides)
    return payload


# ============================================================
# get_current_weather()
# ============================================================


@pytest.mark.asyncio
async def test_get_current_weather_success():

    weather_provider = MockWeatherProvider(
        make_payload()
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

    # Location keeps the existing Nominatim-resolved name (the
    # WeatherAPI name is present in the payload but is not used).
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
    assert result.visibility == 10.0
    assert result.uv_index == 8.0
    assert result.precipitation == 0.0

    # WeatherAPI code 1000 (Clear) -> WMO 0.
    assert result.weather_code == 0
    assert result.weather_condition == "Sunny"

    assert result.rain_probability == 20

    # Sunrise/sunset are parsed in the provider's location timezone.
    tz = ZoneInfo("Asia/Kolkata")

    assert result.sunrise == datetime(
        2026,
        11,
        23,
        6,
        35,
        tzinfo=tz,
    )

    assert result.sunset == datetime(
        2026,
        11,
        23,
        17,
        42,
        tzinfo=tz,
    )


@pytest.mark.asyncio
async def test_get_current_weather_uses_payload_timezone():

    weather_provider = MockWeatherProvider(
        make_payload(
            location={
                "name": "New York",
                "tz_id": "America/New_York",
            }
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=40.7,
        longitude=-74.0,
    )).data

    tz = ZoneInfo("America/New_York")

    assert result.sunrise == datetime(
        2026,
        11,
        23,
        6,
        35,
        tzinfo=tz,
    )

    assert result.sunset == datetime(
        2026,
        11,
        23,
        17,
        42,
        tzinfo=tz,
    )


@pytest.mark.asyncio
async def test_get_current_weather_calls_providers_with_coordinates():

    weather_provider = MockWeatherProvider(
        make_payload()
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
async def test_get_current_weather_uses_provider_name_when_geocode_degraded():

    weather_provider = MockWeatherProvider(
        make_payload()
    )

    location_provider = MockLocationProvider(
        location="Current Location"
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=location_provider,
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.4426,
        longitude=79.9865,
    )).data

    assert result.location == "Nellore"


@pytest.mark.asyncio
async def test_get_current_weather_missing_optionals_become_none():

    # Only the required fields are present; every optional
    # measurement is missing and must map to None (never zero).
    weather_provider = MockWeatherProvider(
        make_payload(
            current={
                "temp_c": 30.0,
                "wind_kph": 10.0,
                "condition": {
                    "code": 1003,
                    "text": "Partly cloudy",
                },
            },
            forecast={
                "forecastday": [
                    {"date": "2026-11-23"}
                ]
            },
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.0,
        longitude=79.0,
    )).data

    assert result.temperature == 30.0
    assert result.wind_speed == 10.0
    assert result.weather_code == 2
    assert result.weather_condition == "Partly cloudy"

    assert result.feels_like is None
    assert result.humidity is None
    assert result.pressure is None
    assert result.visibility is None
    assert result.uv_index is None
    assert result.precipitation is None
    assert result.rain_probability is None
    assert result.sunrise is None
    assert result.sunset is None


@pytest.mark.asyncio
async def test_get_current_weather_unparseable_astro_returns_none():

    weather_provider = MockWeatherProvider(
        make_payload(
            forecast={
                "forecastday": [
                    {
                        "date": "2026-11-23",
                        "day": {"daily_chance_of_rain": 10},
                        "astro": {
                            "sunrise": "not-a-time",
                            "sunset": "05:42 PM",
                        },
                    }
                ]
            }
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.0,
        longitude=79.0,
    )).data

    # Unparseable sunrise -> None; the valid sunset is still parsed.
    assert result.sunrise is None
    assert result.sunset == datetime(
        2026,
        11,
        23,
        17,
        42,
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )


# ============================================================
# WeatherAPI -> WMO code conversion
# ============================================================


@pytest.mark.parametrize(
    "api_code,expected_wmo",
    [
        (1000, 0),   # Clear -> Clear Sky
        (1003, 2),   # Partly cloudy -> Partly Cloudy
        (1006, 3),   # Cloudy -> Overcast
        (1030, 45),  # Mist -> Fog
        (1063, 61),  # Patchy rain possible -> Slight Rain
        (1066, 71),  # Patchy snow possible -> Slight Snow
        (1087, 95),  # Thundery outbreaks possible -> Thunderstorm
        (1183, 61),  # Light rain -> Slight Rain
        (1195, 65),  # Heavy rain -> Heavy Rain
        (1243, 81),  # Moderate/heavy rain shower -> Moderate Rain Showers
        (1276, 95),  # Moderate/heavy rain with thunder -> Thunderstorm
    ],
)
@pytest.mark.asyncio
async def test_weather_code_mapping(api_code, expected_wmo):

    weather_provider = MockWeatherProvider(
        make_payload(
            current={
                "temp_c": 30.0,
                "wind_kph": 10.0,
                "condition": {
                    "code": api_code,
                    "text": "Some condition",
                },
            }
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.0,
        longitude=79.0,
    )).data

    assert result.weather_code == expected_wmo


@pytest.mark.asyncio
async def test_unknown_weather_code_passes_through():

    weather_provider = MockWeatherProvider(
        make_payload(
            current={
                "temp_c": 30.0,
                "wind_kph": 10.0,
                "condition": {
                    "code": 9999,
                    "text": "Mystery weather",
                },
            }
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
        cache=WeatherCache(),
    )

    result = (await service.get_current_weather(
        latitude=14.0,
        longitude=79.0,
    )).data

    assert result.weather_code == 9999


def test_weatherapi_to_wmo_table_has_known_codes():
    # Spot-check the conversion table contents.
    assert WEATHERAPI_TO_WMO[1000] == 0
    assert WEATHERAPI_TO_WMO[1003] == 2
    assert WEATHERAPI_TO_WMO[1066] == 71
    assert WEATHERAPI_TO_WMO[1276] == 95


# ============================================================
# get_weather_recommendation()
# ============================================================


@pytest.mark.asyncio
async def test_get_weather_recommendation_heavy_rain():

    weather_provider = MockWeatherProvider(
        make_payload(
            current={
                "temp_c": 30.0,
                "wind_kph": 10.0,
                "condition": {"code": 1003, "text": "Partly cloudy"},
            },
            forecast={
                "forecastday": [
                    {
                        "date": "2026-11-23",
                        "day": {"daily_chance_of_rain": 80},
                    }
                ]
            },
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
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
        make_payload(
            current={
                "temp_c": 38.0,
                "wind_kph": 10.0,
                "condition": {"code": 1000, "text": "Sunny"},
            },
            forecast={
                "forecastday": [
                    {
                        "date": "2026-11-23",
                        "day": {"daily_chance_of_rain": 10},
                    }
                ]
            },
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
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
        make_payload(
            current={
                "temp_c": 30.0,
                "wind_kph": 10.0,
                "condition": {"code": 1000, "text": "Sunny"},
            },
            forecast={
                "forecastday": [
                    {
                        "date": "2026-11-23",
                        "day": {"daily_chance_of_rain": 10},
                    }
                ]
            },
        )
    )

    service = WeatherService(
        weather_provider=weather_provider,
        location_provider=MockLocationProvider(),
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
