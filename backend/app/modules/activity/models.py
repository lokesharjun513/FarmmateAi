import uuid

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base
from app.shared.mixins import TimestampMixin


if TYPE_CHECKING:

    from app.modules.crop_season.models import CropSeason
    from app.modules.crop_stage.models import CropStage


# ============================================================
# ACTIVITY TYPE
# ============================================================


class ActivityType(str, Enum):

    LAND_PREPARATION = "LAND_PREPARATION"

    SOWING = "SOWING"

    NURSERY = "NURSERY"

    TRANSPLANTING = "TRANSPLANTING"

    IRRIGATION = "IRRIGATION"

    FERTILIZER = "FERTILIZER"

    WEEDING = "WEEDING"

    PEST_CONTROL = "PEST_CONTROL"

    DISEASE_CHECK = "DISEASE_CHECK"

    SPRAYING = "SPRAYING"

    HARVEST = "HARVEST"

    OTHER = "OTHER"


# ============================================================
# ACTIVITY STATUS
# ============================================================


class ActivityStatus(str, Enum):

    PENDING = "PENDING"

    IN_PROGRESS = "IN_PROGRESS"

    COMPLETED = "COMPLETED"

    SKIPPED = "SKIPPED"


# ============================================================
# ACTIVITY SOURCE
# ============================================================


class ActivitySource(str, Enum):

    AI_PLANNED = "AI_PLANNED"

    WEATHER_TRIGGERED = "WEATHER_TRIGGERED"

    FARMER_ADDED = "FARMER_ADDED"

    SYSTEM = "SYSTEM"


# ============================================================
# ACTIVITY PRIORITY
# ============================================================


class ActivityPriority(str, Enum):

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"


# ============================================================
# ACTIVITY
# ============================================================


class Activity(Base, TimestampMixin):

    __tablename__ = "activities"

    # ========================================================
    # TABLE CONSTRAINTS / INDEXES
    # ========================================================

    __table_args__ = (

        # ----------------------------------------------------
        # Estimated duration
        #
        # NULL is allowed.
        #
        # If provided, duration must be >= 1 minute.
        # ----------------------------------------------------

        CheckConstraint(
            """
            estimated_duration_minutes IS NULL
            OR estimated_duration_minutes >= 1
            """,
            name="ck_activity_duration_positive",
        ),

        # ----------------------------------------------------
        # Completed date lifecycle consistency
        #
        # PENDING / IN_PROGRESS
        #     -> completed_date must be NULL
        #
        # COMPLETED / SKIPPED
        #     -> completed_date must NOT be NULL
        # ----------------------------------------------------

        CheckConstraint(
            """
            (
                status IN ('PENDING', 'IN_PROGRESS')
                AND completed_date IS NULL
            )
            OR
            (
                status IN ('COMPLETED', 'SKIPPED')
                AND completed_date IS NOT NULL
            )
            """,
            name="ck_activity_completed_date_consistency",
        ),

        # ----------------------------------------------------
        # CROP + DATE + STATUS
        #
        # Supports:
        #
        # - today's activities
        # - pending activities
        # - dashboard queries
        # - overdue queries
        # ----------------------------------------------------

        Index(
            "ix_activity_crop_date_status",
            "crop_season_id",
            "scheduled_date",
            "status",
        ),

        # ----------------------------------------------------
        # STAGE + DATE
        # ----------------------------------------------------

        Index(
            "ix_activity_stage_date",
            "stage_id",
            "scheduled_date",
        ),

        # ----------------------------------------------------
        # CROP + STATUS + PRIORITY
        # ----------------------------------------------------

        Index(
            "ix_activity_crop_status_priority",
            "crop_season_id",
            "status",
            "priority",
        ),

        # ----------------------------------------------------
        # CROP + SOURCE
        # ----------------------------------------------------

        Index(
            "ix_activity_crop_source",
            "crop_season_id",
            "source",
        ),

        # ----------------------------------------------------
        # DATE + PRIORITY
        # ----------------------------------------------------

        Index(
            "ix_activity_date_priority",
            "scheduled_date",
            "priority",
        ),

        # ----------------------------------------------------
        # CROP + COMPLETED DATE
        #
        # Useful for:
        #
        # - completed history
        # - skipped history
        # - daily completion dashboard
        # ----------------------------------------------------

        Index(
            "ix_activity_crop_completed_date",
            "crop_season_id",
            "completed_date",
        ),

        # ----------------------------------------------------
        # CROP + STAGE + STATUS
        #
        # Useful for:
        #
        # - stage completion checks
        # - unfinished stage activities
        # - stage dashboards
        # ----------------------------------------------------

        Index(
            "ix_activity_crop_stage_status",
            "crop_season_id",
            "stage_id",
            "status",
        ),
    )

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ========================================================
    # CROP SEASON
    # ========================================================
    #
    # Every activity belongs to exactly one crop season.
    #
    # CropSeason deleted
    #     ↓
    # Activities deleted
    #
    # ========================================================

    crop_season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "crop_seasons.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # CROP STAGE
    # ========================================================
    #
    # Optional.
    #
    # CropStage deleted
    #     ↓
    # Activity remains
    # stage_id = NULL
    #
    # ========================================================

    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "crop_stages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================
    # ACTIVITY TYPE
    # ========================================================

    activity_type: Mapped[ActivityType] = mapped_column(
        SqlEnum(
            ActivityType,
            name="activity_type",
            native_enum=True,
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # TITLE
    # ========================================================

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # ========================================================
    # DESCRIPTION
    # ========================================================

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # SCHEDULED DATE
    # ========================================================
    #
    # Current date on which the activity is scheduled.
    #
    # This can change when the activity is rescheduled.
    #
    # ========================================================

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # ========================================================
    # ORIGINAL SCHEDULED DATE
    # ========================================================
    #
    # First scheduled date assigned to the activity.
    #
    # Example:
    #
    # original_scheduled_date = 2026-08-20
    # scheduled_date          = 2026-08-22
    #
    # The activity can also be moved earlier.
    #
    # ========================================================

    original_scheduled_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # ========================================================
    # COMPLETED DATE
    # ========================================================
    #
    # COMPLETED:
    #     actual completion date
    #
    # SKIPPED:
    #     date on which activity was skipped
    #
    # PENDING / IN_PROGRESS:
    #     NULL
    #
    # ========================================================

    completed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    # ========================================================
    # STATUS
    # ========================================================

    status: Mapped[ActivityStatus] = mapped_column(
        SqlEnum(
            ActivityStatus,
            name="activity_status",
            native_enum=True,
        ),
        default=ActivityStatus.PENDING,
        nullable=False,
        index=True,
    )

    # ========================================================
    # PRIORITY
    # ========================================================

    priority: Mapped[ActivityPriority] = mapped_column(
        SqlEnum(
            ActivityPriority,
            name="activity_priority",
            native_enum=True,
        ),
        default=ActivityPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    # ========================================================
    # SOURCE
    # ========================================================

    source: Mapped[ActivitySource] = mapped_column(
        SqlEnum(
            ActivitySource,
            name="activity_source",
            native_enum=True,
        ),
        default=ActivitySource.AI_PLANNED,
        nullable=False,
        index=True,
    )

    # ========================================================
    # NOTES
    # ========================================================

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # ESTIMATED DURATION
    # ========================================================
    #
    # Duration in minutes.
    #
    # Examples:
    #
    # 30
    # 60
    # 120
    #
    # ========================================================

    estimated_duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # CROP SEASON RELATIONSHIP
    # ========================================================

    crop_season: Mapped["CropSeason"] = relationship(
        "CropSeason",
        back_populates="activities",
        passive_deletes=True,
    )

    # ========================================================
    # CROP STAGE RELATIONSHIP
    # ========================================================

    stage: Mapped["CropStage | None"] = relationship(
        "CropStage",
        back_populates="activities",
        passive_deletes=True,
    )