from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.activity.models import (
    ActivityPriority,
    ActivityType,
)

from app.modules.crop_season.models import (
    CropSeasonStatus,
)


# ============================================================
# CROP PLAN ACTIVITY
#
# Represents an activity that will be generated as part of
# the crop plan.
#
# This is an INPUT definition for the plan generator.
#
# It is NOT the database Activity model.
# ============================================================


class CropPlanActivityRequest(BaseModel):

    # --------------------------------------------------------
    # Activity type
    # --------------------------------------------------------

    activity_type: ActivityType

    # --------------------------------------------------------
    # Activity title
    # --------------------------------------------------------

    title: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    # --------------------------------------------------------
    # Relative day
    #
    # The activity date is calculated from the crop
    # sowing/start date.
    #
    # Example:
    #
    # day = 5
    #
    # sowing date = 2026-08-10
    #
    # scheduled date = 2026-08-15
    # --------------------------------------------------------

    day: int = Field(
        ...,
        ge=1,
    )

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    priority: ActivityPriority = (
        ActivityPriority.MEDIUM
    )

    # --------------------------------------------------------
    # Estimated duration
    # --------------------------------------------------------

    estimated_duration_minutes: int | None = Field(
        default=None,
        ge=1,
    )


# ============================================================
# CROP PLAN STAGE
#
# Represents one stage that will be generated.
# ============================================================


class CropPlanStageRequest(BaseModel):

    # --------------------------------------------------------
    # Stage name
    # --------------------------------------------------------

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    # --------------------------------------------------------
    # Stage description
    # --------------------------------------------------------

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    # --------------------------------------------------------
    # Stage order
    #
    # Must start from 1 and remain sequential.
    # --------------------------------------------------------

    stage_order: int = Field(
        ...,
        ge=1,
    )

    # --------------------------------------------------------
    # Relative stage timeline
    # --------------------------------------------------------

    start_day: int = Field(
        ...,
        ge=1,
    )

    end_day: int = Field(
        ...,
        ge=1,
    )

    # --------------------------------------------------------
    # Activities belonging to this stage
    #
    # Optional because activities may also be generated
    # directly against the crop season.
    # --------------------------------------------------------

    activities: list[
        CropPlanActivityRequest
    ] = Field(
        default_factory=list,
    )


# ============================================================
# GENERATE CROP PLAN REQUEST
#
# Used by:
#
# POST /crop-plans/{crop_season_id}/generate
#
# The crop season already contains the crop/farm information.
#
# This request controls the plan generation parameters.
# ============================================================


class CropPlanGenerateRequest(BaseModel):

    # --------------------------------------------------------
    # Sowing/start date
    #
    # Relative activity/stage days are calculated from this
    # date.
    # --------------------------------------------------------

    start_date: date

    # --------------------------------------------------------
    # Optional explicit plan.
    #
    # Later the AI planner can populate this structure.
    #
    # If omitted, the service can use the configured/default
    # crop planning logic.
    # --------------------------------------------------------

    stages: list[
        CropPlanStageRequest
    ] = Field(
        default_factory=list,
    )


# ============================================================
# REGENERATE CROP PLAN REQUEST
#
# Regeneration is only allowed while the crop season is
# PLANNED.
#
# Existing stages and activities will be replaced inside
# one transaction.
# ============================================================


class CropPlanRegenerateRequest(
    CropPlanGenerateRequest
):
    pass


# ============================================================
# GENERATED ACTIVITY RESPONSE
# ============================================================


class CropPlanActivityResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    crop_season_id: UUID

    stage_id: UUID | None

    activity_type: ActivityType

    title: str

    description: str | None

    scheduled_date: date

    original_scheduled_date: date | None

    priority: ActivityPriority

    estimated_duration_minutes: int | None


# ============================================================
# GENERATED STAGE RESPONSE
# ============================================================


class CropPlanStageResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    crop_season_id: UUID

    name: str

    description: str | None

    stage_order: int

    start_day: int

    end_day: int

    # --------------------------------------------------------
    # Activities generated for this stage.
    # --------------------------------------------------------

    activities: list[
        CropPlanActivityResponse
    ] = Field(
        default_factory=list,
    )


# ============================================================
# CROP PLAN RESPONSE
#
# Returned after generating/regenerating a complete plan.
# ============================================================


class CropPlanResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    # --------------------------------------------------------
    # Crop season
    # --------------------------------------------------------

    crop_season_id: UUID

    # --------------------------------------------------------
    # Crop season status
    # --------------------------------------------------------

    status: CropSeasonStatus

    # --------------------------------------------------------
    # Plan start date
    # --------------------------------------------------------

    start_date: date

    # --------------------------------------------------------
    # Generated stages
    # --------------------------------------------------------

    stages: list[
        CropPlanStageResponse
    ] = Field(
        default_factory=list,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_stages: int

    total_activities: int