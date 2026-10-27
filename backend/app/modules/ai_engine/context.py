from pydantic import BaseModel


class AIContext(BaseModel):
    crop_name: str

    crop_variety: str | None = None

    crop_age_days: int

    soil_type: str | None = None

    location: str

    weather: str

    temperature: float

    humidity: int

    rain_probability: int

    today_activities: list[str]

    language: str = "English"