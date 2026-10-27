from enum import Enum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ============================================================
# ACTIVITY PRIORITY
# ============================================================


class ActivityPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================
# AI ACTIVITY
# ============================================================


class AIActivity(BaseModel):

    day: int = Field(
        ...,
        ge=1,
    )

    title: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    activity_type: str = Field(
        ...,
        min_length=2,
        max_length=50,
    )

    description: str = Field(
        ...,
        min_length=2,
        max_length=1000,
    )

    priority: ActivityPriority

    estimated_duration_minutes: int = Field(
        ...,
        ge=1,
        le=1440,
    )


# ============================================================
# AI CROP STAGE
# ============================================================


class AICropStage(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    description: str = Field(
        ...,
        min_length=2,
        max_length=1000,
    )

    stage_order: int = Field(
        ...,
        ge=1,
    )

    start_day: int = Field(
        ...,
        ge=1,
    )

    end_day: int = Field(
        ...,
        ge=1,
    )

    activities: list[AIActivity] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_days(self):

        if self.end_day < self.start_day:
            raise ValueError(
                "Stage end day must be greater than "
                "or equal to stage start day."
            )

        if not self.activities:
            raise ValueError(
                f"Stage '{self.name}' must contain "
                "at least one activity."
            )

        for activity in self.activities:

            if activity.day < self.start_day:
                raise ValueError(
                    f"Activity '{activity.title}' occurs "
                    f"before stage start day."
                )

            if activity.day > self.end_day:
                raise ValueError(
                    f"Activity '{activity.title}' occurs "
                    f"after stage end day."
                )

        return self


# ============================================================
# CROP PLAN
# ============================================================


class CropPlanResponse(BaseModel):

    crop_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    crop_variety: str | None = Field(
        default=None,
        max_length=100,
    )

    season: str = Field(
        ...,
        min_length=2,
        max_length=30,
    )

    estimated_duration_days: int = Field(
        ...,
        ge=1,
        le=1000,
    )

    stages: list[AICropStage] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_stages(self):

        if not self.stages:
            raise ValueError(
                "Crop plan must contain at least one stage."
            )

        orders = [
            stage.stage_order
            for stage in self.stages
        ]

        if len(orders) != len(set(orders)):
            raise ValueError(
                "Crop stage orders must be unique."
            )

        expected_orders = list(
            range(
                1,
                len(orders) + 1,
            )
        )

        if sorted(orders) != expected_orders:
            raise ValueError(
                "Crop stage orders must start at 1 "
                "and be sequential."
            )

        for stage in self.stages:

            if stage.end_day > self.estimated_duration_days:
                raise ValueError(
                    f"Stage '{stage.name}' extends "
                    "beyond crop duration."
                )

        return self


# ============================================================
# GENERATE CROP PLAN REQUEST
# ============================================================


class CropPlanGenerateRequest(BaseModel):

    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    district: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    village: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    soil_type: str | None = Field(
        default=None,
        max_length=100,
    )


# ============================================================
# GENERATED PLAN RESULT
#
# Used by API if you want to return persistence information.
# ============================================================


class CropPlanGenerateResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    crop_season_id: UUID

    crop_name: str

    crop_variety: str | None

    season: str

    estimated_duration_days: int

    stages_created: int

    activities_created: int