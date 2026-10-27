from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.crop_season.schemas import FarmingSeason


# ============================================================
# GENERATE FARMING PLAN
# ============================================================


class GenerateFarmingPlanRequest(BaseModel):
    farm_id: UUID

    crop_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    crop_variety: str | None = Field(
        default=None,
        max_length=100,
    )

    season: FarmingSeason

    sowing_date: date

    land_area: float = Field(
        ...,
        gt=0,
    )

    land_unit: str = Field(
        default="Acres",
        max_length=20,
    )


class PlanActivity(BaseModel):
    day: int

    title: str

    activity_type: str

    description: str

    priority: str

    estimated_duration_minutes: int


class PlanStage(BaseModel):
    name: str

    description: str

    stage_order: int

    start_day: int

    end_day: int

    activities: list[PlanActivity]


class GenerateFarmingPlanResponse(BaseModel):
    crop_name: str

    crop_variety: str | None

    season: FarmingSeason

    sowing_date: date

    estimated_duration_days: int

    stages: list[PlanStage]


# ============================================================
# START FARMING
# ============================================================


class StartFarmingRequest(BaseModel):
    farm_id: UUID

    crop_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    crop_variety: str | None = Field(
        default=None,
        max_length=100,
    )

    season: FarmingSeason

    sowing_date: date

    land_area: float = Field(
        ...,
        gt=0,
    )

    land_unit: str = Field(
        default="Acres",
        max_length=20,
    )

    stages: list[PlanStage]


class StartFarmingResponse(BaseModel):
    crop_season_id: UUID

    crop_name: str

    crop_variety: str | None

    season: FarmingSeason

    sowing_date: date

    estimated_duration_days: int

    total_stages: int

    total_activities: int

    message: str