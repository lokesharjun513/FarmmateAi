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
    UniqueConstraint,
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

    from app.modules.activity.models import Activity
    from app.modules.crop_season.models import CropSeason


# ============================================================
# CROP STAGE STATUS
# ============================================================

class CropStageStatus(str, Enum):

    # Crop plan exists, but farmer has not started this stage.
    PENDING = "PENDING"

    # Farmer is currently working on this stage.
    ACTIVE = "ACTIVE"

    # Farmer completed this stage.
    COMPLETED = "COMPLETED"

    # Farmer intentionally skipped this stage.
    SKIPPED = "SKIPPED"


# ============================================================
# CROP STAGE
# ============================================================

class CropStage(Base, TimestampMixin):

    __tablename__ = "crop_stages"

    # ========================================================
    # TABLE CONSTRAINTS / INDEXES
    # ========================================================

    __table_args__ = (

        # ----------------------------------------------------
        # A crop season cannot have duplicate stage orders.
        #
        # Example:
        #
        # Stage 1 -> allowed
        # Stage 2 -> allowed
        # Stage 2 -> NOT allowed
        # ----------------------------------------------------

        UniqueConstraint(
            "crop_season_id",
            "stage_order",
            name="uq_crop_stage_season_order",
        ),

        # ----------------------------------------------------
        # Stage order must start from 1.
        # ----------------------------------------------------

        CheckConstraint(
            "stage_order >= 1",
            name="ck_crop_stage_order_positive",
        ),

        # ----------------------------------------------------
        # Stage timeline must start from day 1 or later.
        # ----------------------------------------------------

        CheckConstraint(
            "start_day >= 1",
            name="ck_crop_stage_start_day_positive",
        ),

        # ----------------------------------------------------
        # End day must be at least day 1.
        # ----------------------------------------------------

        CheckConstraint(
            "end_day >= 1",
            name="ck_crop_stage_end_day_positive",
        ),

        # ----------------------------------------------------
        # End day cannot be before start day.
        # ----------------------------------------------------

        CheckConstraint(
            "end_day >= start_day",
            name="ck_crop_stage_valid_timeline",
        ),

        # ----------------------------------------------------
        # Frequently used query:
        #
        # crop_season_id + status
        #
        # Example:
        #
        # Get active stage for a crop.
        # Get pending stages.
        # ----------------------------------------------------

        Index(
            "ix_crop_stage_season_status",
            "crop_season_id",
            "status",
        ),

        # ----------------------------------------------------
        # Frequently used query:
        #
        # crop_season_id + stage_order
        # ----------------------------------------------------

        Index(
            "ix_crop_stage_season_order",
            "crop_season_id",
            "stage_order",
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
    # STAGE INFORMATION
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # STAGE ORDER
    #
    # Example:
    #
    # 1 -> Land Preparation
    # 2 -> Nursery
    # 3 -> Transplanting
    # 4 -> Vegetative Growth
    # 5 -> Flowering
    # 6 -> Harvest
    # ========================================================

    stage_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # RELATIVE TIMELINE
    #
    # Timeline is relative to crop sowing date.
    #
    # Example:
    #
    # start_day = 1
    # end_day   = 10
    #
    # Stage expected around days 1-10.
    # ========================================================

    start_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # STATUS
    #
    # Lifecycle:
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
    #
    # IMPORTANT:
    #
    # Status changes are controlled by service.py.
    # ========================================================

    status: Mapped[CropStageStatus] = mapped_column(
        SqlEnum(
            CropStageStatus,
            name="crop_stage_status",
        ),
        default=CropStageStatus.PENDING,
        nullable=False,
        index=True,
    )

    # ========================================================
    # ACTUAL STAGE DATES
    # ========================================================

    started_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    completed_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # ========================================================
    # CROP SEASON RELATIONSHIP
    # ========================================================

    crop_season: Mapped["CropSeason"] = relationship(
        "CropSeason",
        back_populates="stages",
    )

    # ========================================================
    # ACTIVITIES
    #
    # Activities belong to CropSeason.
    #
    # An activity can optionally reference a stage.
    #
    # CropSeason
    #      │
    #      ├── Activity
    #      │
    #      └── CropStage
    #               │
    #               └── Activity.stage
    #
    # This allows farming history to remain independent
    # from a stage.
    # ========================================================

    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="stage",
    )