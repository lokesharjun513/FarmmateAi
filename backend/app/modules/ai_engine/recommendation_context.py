from pydantic import BaseModel

from app.modules.weather.schemas import CurrentWeatherResponse


class RecommendationContext(BaseModel):

    state: str
    district: str
    mandal: str
    village: str

    season: str

    land_area: float
    land_unit: str

    soil_type: str | None
    water_source: str | None
    water_availability: str | None
    irrigation_method: str | None

    latitude: float
    longitude: float

    weather: CurrentWeatherResponse