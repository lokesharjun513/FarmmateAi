from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CurrentWeatherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location: str

    latitude: float
    longitude: float

    temperature: float
    feels_like: float | None = None

    humidity: int | None = None

    wind_speed: float

    pressure: float | None = None

    visibility: float | None = None

    uv_index: float | None = None

    precipitation: float | None = None

    weather_code: int

    weather_condition: str

    rain_probability: int | None = None

    sunrise: datetime | None = None

    sunset: datetime | None = None


class ForecastDay(BaseModel):
    date: datetime
    min_temperature: float
    max_temperature: float
    weather_condition: str
    rain_probability: int | None = None


class ForecastResponse(BaseModel):
    days: list[ForecastDay]


class WeatherRecommendationResponse(BaseModel):
    recommendation: str
    priority: str