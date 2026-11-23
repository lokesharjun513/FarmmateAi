from fastapi import APIRouter, Query

from app.modules.weather.schemas import (
    CurrentWeatherResponse,
    WeatherRecommendationResponse,
)
from app.modules.weather.service import WeatherService

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.get(
    "/current",
    response_model=ApiResponse[CurrentWeatherResponse],
)
async def current_weather(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
    location: str | None = Query(
        None,
        min_length=2,
        max_length=100,
    ),
):

    service = WeatherService()

    weather_result = await service.get_current_weather(
        latitude=latitude,
        longitude=longitude,
        location=location,
    )

    message = "Current weather retrieved successfully."

    if weather_result.stale:
        message = (
            "Current weather retrieved successfully. "
            "Showing last available weather data "
            "(may be up to 6 hours old)."
        )

    return ApiResponse(
        success=True,
        message=message,
        data=weather_result.data,
    )


@router.get(
    "/recommendation",
    response_model=ApiResponse[WeatherRecommendationResponse],
)
async def weather_recommendation(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
    location: str | None = Query(
        None,
        min_length=2,
        max_length=100,
    ),
):

    service = WeatherService()

    recommendation = await service.get_weather_recommendation(
        latitude=latitude,
        longitude=longitude,
        location=location,
    )

    return ApiResponse(
        success=True,
        message="Weather recommendation generated successfully.",
        data=recommendation,
    )