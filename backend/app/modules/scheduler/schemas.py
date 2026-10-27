from pydantic import BaseModel


class SchedulerRunResponse(BaseModel):
    processed_farms: int

    processed_crop_seasons: int

    weather_updated: int

    advisor_generated: int

    notifications_created: int

    expired_sessions: int

    completed: bool