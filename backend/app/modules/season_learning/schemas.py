from datetime import datetime

from pydantic import BaseModel


class SchedulerRunResponse(BaseModel):
    processed_farms: int

    active_crop_seasons: int

    weather_updated: int

    activities_created: int

    advisors_generated: int

    notifications_created: int

    expired_chat_sessions: int

    completed: bool


class SchedulerStatusResponse(BaseModel):
    last_run: datetime | None = None

    next_run: datetime | None = None

    is_running: bool

    status: str


class SchedulerStatisticsResponse(BaseModel):
    total_runs: int

    successful_runs: int

    failed_runs: int

    average_duration_seconds: float

class ActivitySchedulerResult(BaseModel):
    active_crop_seasons: int
    activities_created: int


class WeatherSchedulerResult(BaseModel):
    processed_farms: int
    weather_updated: int


class AdvisorSchedulerResult(BaseModel):
    advisors_generated: int


class NotificationSchedulerResult(BaseModel):
    notifications_created: int


class CleanupSchedulerResult(BaseModel):
    expired_chat_sessions: int