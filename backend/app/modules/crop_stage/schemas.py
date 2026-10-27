from datetime import date
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.modules.crop_stage.models import (
    CropStageStatus,
)


# ============================================================
# CREATE CROP STAGE
#
# Used for:
#
# 1. AI-generated crop plans
# 2. Farmer manually adding a stage
#
# Newly created stage:
#
# PENDING
#
# Status cannot be supplied by the client.
# The backend always creates a new stage as PENDING.
# ============================================================


class CropStageCreateRequest(BaseModel):

    # ========================================================
    # STAGE INFORMATION
    # ========================================================

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    # ========================================================
    # STAGE ORDER
    #
    # Example:
    #
    # 1 = Land Preparation
    # 2 = Nursery
    # 3 = Transplanting
    # 4 = Vegetative Growth
    #
    # Service layer ensures stages are continuous.
    # ========================================================

    stage_order: int = Field(
        ...,
        ge=1,
    )

    # ========================================================
    # RELATIVE TIMELINE
    #
    # Days are relative to crop sowing date.
    #
    # Example:
    #
    # start_day = 1
    # end_day = 10
    #
    # means the stage is expected around days 1-10.
    # ========================================================

    start_day: int = Field(
        ...,
        ge=1,
    )

    end_day: int = Field(
        ...,
        ge=1,
    )

    # ========================================================
    # VALIDATE TIMELINE
    # ========================================================

    @model_validator(mode="after")
    def validate_days(self):

        if self.end_day < self.start_day:

            raise ValueError(
                "End day must be greater than or equal "
                "to start day."
            )

        return self


# ============================================================
# UPDATE CROP STAGE
#
# Only PLANNED crop seasons can be modified.
#
# Only PENDING stages can be modified.
#
# Lifecycle fields are intentionally NOT accepted.
#
# The client cannot modify:
#
# - status
# - started_at
# - completed_at
#
# Lifecycle is controlled by:
#
# /activate
# /complete
# /skip
# ============================================================


class CropStageUpdateRequest(BaseModel):

    # ========================================================
    # STAGE INFORMATION
    # ========================================================

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    # ========================================================
    # STAGE ORDER
    #
    # Accepted for backward compatibility.
    #
    # Service layer currently prevents changing the order
    # after the stage has been created.
    # ========================================================

    stage_order: int | None = Field(
        default=None,
        ge=1,
    )

    # ========================================================
    # RELATIVE TIMELINE
    # ========================================================

    start_day: int | None = Field(
        default=None,
        ge=1,
    )

    end_day: int | None = Field(
        default=None,
        ge=1,
    )

    # ========================================================
    # VALIDATE TIMELINE
    #
    # If both values are provided, validate immediately.
    #
    # If only one is provided, service.py compares it with
    # the existing database value.
    # ========================================================

    @model_validator(mode="after")
    def validate_days(self):

        if (
            self.start_day is not None
            and self.end_day is not None
            and self.end_day < self.start_day
        ):

            raise ValueError(
                "End day must be greater than or equal "
                "to start day."
            )

        return self


# ============================================================
# CROP STAGE RESPONSE
#
# Returned to:
#
# - Mobile application
# - Web frontend
# - Dashboard
# - AI assistant
#
# Status lifecycle:
#
# PENDING
#    ↓
# ACTIVE
#    ↓
# COMPLETED
#
# OR
#
# PENDING
#    ↓
# ACTIVE
#    ↓
# SKIPPED
# ============================================================


class CropStageResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ========================================================
    # IDENTITY
    # ========================================================

    id: UUID

    crop_season_id: UUID

    # ========================================================
    # STAGE INFORMATION
    # ========================================================

    name: str

    description: str | None

    stage_order: int

    # ========================================================
    # RELATIVE TIMELINE
    #
    # Timeline relative to crop sowing date.
    # ========================================================

    start_day: int

    end_day: int

    # ========================================================
    # LIFECYCLE STATUS
    #
    # PENDING:
    # Stage is planned but not started.
    #
    # ACTIVE:
    # Farmer is currently working on this stage.
    #
    # COMPLETED:
    # Farmer completed this stage.
    #
    # SKIPPED:
    # Farmer skipped this stage.
    # ========================================================

    status: CropStageStatus

    # ========================================================
    # ACTUAL EXECUTION DATES
    #
    # started_at:
    # Actual date the stage became ACTIVE.
    #
    # completed_at:
    # Actual date the stage was COMPLETED or SKIPPED.
    # ========================================================

    started_at: date | None

    completed_at: date | None