from datetime import datetime

import pytest
from pydantic import ValidationError

from app.modules.weather.schemas import (
    CurrentWeatherResponse,
    ForecastDay,
    ForecastResponse,
    WeatherRecommendationResponse,
)


def test_current_weather_response_valid():
    data = {
        "location": "Nellore",
        "latitude": 14.4426,
        "longitude": 79.9865,
        "temperature": 32.5,
        "feels_like": 35.2,
        "humidity": 72,
        "wind_speed": 12.5,
        "pressure": 1008.2,
        "visibility": 10.0,
        "uv_index": 7.5,
        "precipitation": 0.2,
        "weather_code": 63,
        "weather_condition": "Moderate Rain",
        "rain_probability": 70,
        "sunrise": datetime(2026, 8, 15, 6, 0),
        "sunset": datetime(2026, 8, 15, 18, 30),
    }

    result = CurrentWeatherResponse(**data)

    assert result.location == "Nellore"
    assert result.latitude == 14.4426
    assert result.longitude == 79.9865
    assert result.temperature == 32.5
    assert result.feels_like == 35.2
    assert result.humidity == 72
    assert result.wind_speed == 12.5
    assert result.weather_code == 63
    assert result.weather_condition == "Moderate Rain"
    assert result.rain_probability == 70


def test_current_weather_response_optional_fields_default_to_none():
    data = {
        "location": "Nellore",
        "latitude": 14.4426,
        "longitude": 79.9865,
        "temperature": 32.5,
        "wind_speed": 10.0,
        "weather_code": 0,
        "weather_condition": "Clear Sky",
    }

    result = CurrentWeatherResponse(**data)

    assert result.feels_like is None
    assert result.humidity is None
    assert result.pressure is None
    assert result.visibility is None
    assert result.uv_index is None
    assert result.precipitation is None
    assert result.rain_probability is None
    assert result.sunrise is None
    assert result.sunset is None


@pytest.mark.parametrize(
    "field",
    [
        "location",
        "latitude",
        "longitude",
        "temperature",
        "wind_speed",
        "weather_code",
        "weather_condition",
    ],
)
def test_current_weather_required_fields(field):
    data = {
        "location": "Nellore",
        "latitude": 14.4426,
        "longitude": 79.9865,
        "temperature": 32.5,
        "wind_speed": 10.0,
        "weather_code": 0,
        "weather_condition": "Clear Sky",
    }

    del data[field]

    with pytest.raises(ValidationError):
        CurrentWeatherResponse(**data)


def test_current_weather_from_attributes_config():
    assert CurrentWeatherResponse.model_config["from_attributes"] is True


def test_forecast_day_valid():
    forecast = ForecastDay(
        date=datetime(2026, 8, 15),
        min_temperature=25.0,
        max_temperature=33.5,
        weather_condition="Partly Cloudy",
        rain_probability=40,
    )

    assert forecast.date == datetime(2026, 8, 15)
    assert forecast.min_temperature == 25.0
    assert forecast.max_temperature == 33.5
    assert forecast.weather_condition == "Partly Cloudy"
    assert forecast.rain_probability == 40


def test_forecast_day_rain_probability_is_optional():
    forecast = ForecastDay(
        date=datetime(2026, 8, 15),
        min_temperature=25.0,
        max_temperature=33.5,
        weather_condition="Clear Sky",
    )

    assert forecast.rain_probability is None


def test_forecast_response_valid():
    days = [
        ForecastDay(
            date=datetime(2026, 8, 15),
            min_temperature=25.0,
            max_temperature=33.0,
            weather_condition="Clear Sky",
            rain_probability=10,
        ),
        ForecastDay(
            date=datetime(2026, 8, 16),
            min_temperature=26.0,
            max_temperature=34.0,
            weather_condition="Moderate Rain",
            rain_probability=70,
        ),
    ]

    result = ForecastResponse(days=days)

    assert len(result.days) == 2
    assert result.days[0].weather_condition == "Clear Sky"
    assert result.days[1].rain_probability == 70


def test_forecast_response_defaults_to_required_days():
    with pytest.raises(ValidationError):
        ForecastResponse()


def test_forecast_response_accepts_empty_days():
    result = ForecastResponse(days=[])

    assert result.days == []


def test_weather_recommendation_response_valid():
    result = WeatherRecommendationResponse(
        recommendation="Avoid spraying pesticides today because rain is expected.",
        priority="high",
    )

    assert (
        result.recommendation
        == "Avoid spraying pesticides today because rain is expected."
    )
    assert result.priority == "high"


def test_weather_recommendation_response_requires_recommendation():
    with pytest.raises(ValidationError):
        WeatherRecommendationResponse(priority="high")


def test_weather_recommendation_response_requires_priority():
    with pytest.raises(ValidationError):
        WeatherRecommendationResponse(
            recommendation="Rain is expected."
        )