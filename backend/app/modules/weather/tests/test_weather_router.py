import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.weather.router import router
from app.modules.weather.service import WeatherResult
from app.modules.weather.schemas import (
    CurrentWeatherResponse,
    WeatherRecommendationResponse,
)


app = FastAPI()

app.include_router(router)


# ============================================================
# Helpers
# ============================================================


def create_current_weather():

    return CurrentWeatherResponse(
        location="Nellore, Andhra Pradesh",
        latitude=14.4426,
        longitude=79.9865,
        temperature=32.5,
        feels_like=35.0,
        humidity=70,
        wind_speed=12.0,
        pressure=1008.0,
        visibility=None,
        uv_index=None,
        precipitation=0.0,
        weather_code=0,
        weather_condition="Clear Sky",
        rain_probability=20,
        sunrise="2026-08-15T05:45:00",
        sunset="2026-08-15T18:30:00",
    )


def create_recommendation():

    return WeatherRecommendationResponse(
        recommendation=(
            "Weather conditions look suitable "
            "for normal farm activities today."
        ),
        priority="low",
    )


class MockWeatherService:

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        location: str | None = None,
    ):

        return WeatherResult(
            data=create_current_weather(),
        )

    async def get_weather_recommendation(
        self,
        latitude: float,
        longitude: float,
        location: str | None = None,
    ):

        return create_recommendation()


# ============================================================
# Current Weather
# ============================================================


def test_current_weather_success(monkeypatch):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": 14.4426,
            "longitude": 79.9865,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert (
        data["message"]
        == "Current weather retrieved successfully."
    )

    assert data["data"]["location"] == (
        "Nellore, Andhra Pradesh"
    )

    assert data["data"]["latitude"] == 14.4426
    assert data["data"]["longitude"] == 79.9865

    assert data["data"]["temperature"] == 32.5
    assert data["data"]["weather_code"] == 0
    assert data["data"]["weather_condition"] == (
        "Clear Sky"
    )


def test_current_weather_with_location(monkeypatch):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": 14.4426,
            "longitude": 79.9865,
            "location": "Nellore",
        },
    )

    assert response.status_code == 200


# ============================================================
# Current Weather Validation
# ============================================================


@pytest.mark.parametrize(
    "latitude",
    [
        -90,
        90,
    ],
)
def test_current_weather_valid_latitude(
    monkeypatch,
    latitude,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": latitude,
            "longitude": 79,
        },
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "longitude",
    [
        -180,
        180,
    ],
)
def test_current_weather_valid_longitude(
    monkeypatch,
    longitude,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": 14,
            "longitude": longitude,
        },
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "latitude",
    [
        -90.1,
        90.1,
    ],
)
def test_current_weather_invalid_latitude(
    monkeypatch,
    latitude,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": latitude,
            "longitude": 79,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "longitude",
    [
        -180.1,
        180.1,
    ],
)
def test_current_weather_invalid_longitude(
    monkeypatch,
    longitude,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": 14,
            "longitude": longitude,
        },
    )

    assert response.status_code == 422


def test_current_weather_missing_latitude(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "longitude": 79,
        },
    )

    assert response.status_code == 422


def test_current_weather_missing_longitude(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": 14,
        },
    )

    assert response.status_code == 422


def test_current_weather_invalid_location_too_short(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": 14,
            "longitude": 79,
            "location": "A",
        },
    )

    assert response.status_code == 422


def test_current_weather_invalid_location_too_long(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/current",
        params={
            "latitude": 14,
            "longitude": 79,
            "location": "A" * 101,
        },
    )

    assert response.status_code == 422


# ============================================================
# Recommendation
# ============================================================


def test_weather_recommendation_success(monkeypatch):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/recommendation",
        params={
            "latitude": 14.4426,
            "longitude": 79.9865,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert (
        data["message"]
        == "Weather recommendation generated successfully."
    )

    assert data["data"]["priority"] == "low"

    assert (
        data["data"]["recommendation"]
        == (
            "Weather conditions look suitable "
            "for normal farm activities today."
        )
    )


def test_weather_recommendation_with_location(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/recommendation",
        params={
            "latitude": 14.4426,
            "longitude": 79.9865,
            "location": "Nellore",
        },
    )

    assert response.status_code == 200


def test_weather_recommendation_invalid_latitude(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/recommendation",
        params={
            "latitude": 91,
            "longitude": 79,
        },
    )

    assert response.status_code == 422


def test_weather_recommendation_invalid_longitude(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/recommendation",
        params={
            "latitude": 14,
            "longitude": 181,
        },
    )

    assert response.status_code == 422


def test_weather_recommendation_missing_latitude(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/recommendation",
        params={
            "longitude": 79,
        },
    )

    assert response.status_code == 422


def test_weather_recommendation_missing_longitude(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        lambda: MockWeatherService(),
    )

    client = TestClient(app)

    response = client.get(
        "/weather/recommendation",
        params={
            "latitude": 14,
        },
    )

    assert response.status_code == 422