from datetime import date, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.activity.models import (
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
    ActivityType,
)


# ============================================================
# CREATE ACTIVITY
#
# Farmer-facing request.
#
# Backend automatically controls:
#
# - status
# - source
# - completed_date
# - original_scheduled_date
#
# New farmer activity:
#
# status = PENDING
# source = FARMER_ADDED
#
# ============================================================


class ActivityCreateRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    # ========================================================
    # CROP STAGE
    #
    # Optional.
    #
    # None = crop-level activity.
    #
    # ========================================================

    stage_id: UUID | None = None

    # ========================================================
    # ACTIVITY TYPE
    # ========================================================

    activity_type: ActivityType

    # ========================================================
    # TITLE
    # ========================================================

    title: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Activity title must contain at least "
                "2 non-space characters."
            )

        return value

    # ========================================================
    # DESCRIPTION
    # ========================================================

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value if value else None

    # ========================================================
    # SCHEDULED DATE
    # ========================================================

    scheduled_date: date

    # ========================================================
    # NOTES
    # ========================================================

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value if value else None

    # ========================================================
    # PRIORITY
    # ========================================================

    priority: ActivityPriority = (
        ActivityPriority.MEDIUM
    )

    # ========================================================
    # ESTIMATED DURATION
    #
    # Minutes.
    #
    # NULL = not specified.
    #
    # ========================================================

    estimated_duration_minutes: int | None = Field(
        default=None,
        ge=1,
    )


# ============================================================
# INTERNAL ACTIVITY CREATE
#
# Used by trusted backend systems:
#
# - AI Planner
# - Weather Service
# - Scheduler
# - System automation
#
# IMPORTANT:
#
# source is controlled by trusted backend code.
#
# Farmer-facing API must NEVER use this schema directly.
#
# ============================================================


class ActivityInternalCreateRequest(
    ActivityCreateRequest
):

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    # ========================================================
    # ACTIVITY SOURCE
    # ========================================================

    source: ActivitySource = (
        ActivitySource.AI_PLANNED
    )


# ============================================================
# UPDATE ACTIVITY
#
# Only editable fields are accepted.
#
# NOT accepted:
#
# - status
# - completed_date
# - source
# - original_scheduled_date
#
# Those fields are controlled by service lifecycle
# operations.
#
# ============================================================


class ActivityUpdateRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    # ========================================================
    # CROP STAGE
    #
    # Optional.
    #
    # IMPORTANT:
    #
    # These two requests have different meanings:
    #
    # {}
    #
    #     Do not change stage.
    #
    #
    # {
    #     "stage_id": null
    # }
    #
    #     Remove activity from its current stage.
    #
    # The service detects this using:
    #
    # request.model_dump(exclude_unset=True)
    #
    # ========================================================

    stage_id: UUID | None = None

    # ========================================================
    # ACTIVITY TYPE
    # ========================================================

    activity_type: ActivityType | None = None

    # ========================================================
    # TITLE
    # ========================================================

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Activity title must contain at least "
                "2 non-space characters."
            )

        return value

    # ========================================================
    # DESCRIPTION
    # ========================================================

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value if value else None

    # ========================================================
    # SCHEDULED DATE
    #
    # Allows rescheduling.
    #
    # The service preserves:
    #
    # original_scheduled_date
    #
    # ========================================================

    scheduled_date: date | None = None

    # ========================================================
    # NOTES
    # ========================================================

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value if value else None

    # ========================================================
    # PRIORITY
    # ========================================================

    priority: ActivityPriority | None = None

    # ========================================================
    # ESTIMATED DURATION
    # ========================================================

    estimated_duration_minutes: int | None = Field(
        default=None,
        ge=1,
    )


# ============================================================
# ACTIVITY RESPONSE
#
# Complete API representation.
#
# ============================================================


class ActivityResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ========================================================
    # IDENTITY
    # ========================================================

    id: UUID

    crop_season_id: UUID

    stage_id: UUID | None

    # ========================================================
    # ACTIVITY INFORMATION
    # ========================================================

    activity_type: ActivityType

    title: str

    description: str | None

    # ========================================================
    # SCHEDULE
    # ========================================================

    scheduled_date: date

    original_scheduled_date: date | None

    # ========================================================
    # COMPLETION
    # ========================================================

    completed_date: date | None

    # ========================================================
    # LIFECYCLE
    # ========================================================

    status: ActivityStatus

    # ========================================================
    # ADDITIONAL INFORMATION
    # ========================================================

    notes: str | None

    priority: ActivityPriority

    estimated_duration_minutes: int | None

    # ========================================================
    # SOURCE
    # ========================================================

    source: ActivitySource

    # ========================================================
    # TIMESTAMPS
    #
    # Provided by TimestampMixin.
    #
    # ========================================================

    created_at: datetime | None = None

    updated_at: datetime | None = None