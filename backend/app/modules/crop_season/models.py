import uuid

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum as SqlEnum,
    Float,
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

    from app.modules.farm.models import Farm
    from app.modules.activity.models import Activity
    from app.modules.crop_stage.models import CropStage


# ============================================================
# CROP SEASON STATUS
# ============================================================
#
# PLANNED
#     Crop has been selected/planned but cultivation has not
#     started yet.
#
# ACTIVE
#     Farmer is currently cultivating this crop.
#
# HARVESTED
#     Crop lifecycle has been completed successfully.
#
# CANCELLED
#     Crop plan was cancelled before completion.
#
# ============================================================


class CropSeasonStatus(str, Enum):

    PLANNED = "PLANNED"

    ACTIVE = "ACTIVE"

    HARVESTED = "HARVESTED"

    CANCELLED = "CANCELLED"


# ============================================================
# FARMING SEASON
# ============================================================
#
# KHARIF
#     Monsoon season.
#
# RABI
#     Winter season.
#
# ZAID
#     Summer season.
#
# ============================================================


class FarmingSeason(str, Enum):

    KHARIF = "KHARIF"

    RABI = "RABI"

    ZAID = "ZAID"


# ============================================================
# CROP SEASON
# ============================================================
#
# Represents one complete farming cycle for one crop on a farm.
#
# Farm
#   │
#   ├── Crop Season
#   │      ├── Crop Stages
#   │      └── Activities
#   │
#   └── Crop Season
#
#
# Lifecycle:
#
#     PLANNED
#        ↓
#     ACTIVE
#        ↓
#     HARVESTED
#
# Or:
#
#     PLANNED
#        ↓
#     CANCELLED
#
# ============================================================


class CropSeason(Base, TimestampMixin):

    __tablename__ = "crop_seasons"

    # ========================================================
    # TABLE CONSTRAINTS / INDEXES
    # ========================================================

    __table_args__ = (

        # ----------------------------------------------------
        # Land area must always be positive.
        # ----------------------------------------------------

        CheckConstraint(
            "land_area > 0",
            name="ck_crop_season_land_area_positive",
        ),

        # ----------------------------------------------------
        # Farming year must be valid.
        # ----------------------------------------------------

        CheckConstraint(
            "year >= 2000",
            name="ck_crop_season_year_valid",
        ),

        # ----------------------------------------------------
        # Expected harvest date cannot be before sowing date.
        #
        # NULL is allowed because expected harvest date is
        # optional.
        # ----------------------------------------------------

        CheckConstraint(
            """
            expected_harvest_date IS NULL
            OR expected_harvest_date >= sowing_date
            """,
            name="ck_crop_season_expected_harvest_valid",
        ),

        # ----------------------------------------------------
        # Actual harvest date cannot be before sowing date.
        #
        # NULL is allowed until the crop is harvested.
        # ----------------------------------------------------

        CheckConstraint(
            """
            harvested_date IS NULL
            OR harvested_date >= sowing_date
            """,
            name="ck_crop_season_harvested_date_valid",
        ),

        # ----------------------------------------------------
        # FARM + STATUS
        #
        # Useful for queries such as:
        #
        # "Give me all ACTIVE crops for this farm."
        # ----------------------------------------------------

        Index(
            "ix_crop_season_farm_status",
            "farm_id",
            "status",
        ),

        # ----------------------------------------------------
        # FARM + YEAR
        #
        # Useful for historical crop-season queries.
        # ----------------------------------------------------

        Index(
            "ix_crop_season_farm_year",
            "farm_id",
            "year",
        ),

        # ----------------------------------------------------
        # FARM + FARMING SEASON
        # ----------------------------------------------------

        Index(
            "ix_crop_season_farm_season",
            "farm_id",
            "season",
        ),

        # ----------------------------------------------------
        # SOWING DATE
        # ----------------------------------------------------

        Index(
            "ix_crop_season_sowing_date",
            "sowing_date",
        ),

        # ----------------------------------------------------
        # EXPECTED HARVEST DATE
        # ----------------------------------------------------

        Index(
            "ix_crop_season_expected_harvest_date",
            "expected_harvest_date",
        ),

        # ----------------------------------------------------
        # ACTUAL HARVEST DATE
        # ----------------------------------------------------

        Index(
            "ix_crop_season_harvested_date",
            "harvested_date",
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
    # FARM
    #
    # Every crop season belongs to exactly one farm.
    #
    # Deleting the farm deletes its crop seasons.
    # ========================================================

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # CROP INFORMATION
    # ========================================================

    crop_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    crop_variety: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ========================================================
    # LAND ALLOCATION
    # ========================================================

    land_area: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    land_unit: Mapped[str] = mapped_column(
        String(20),
        default="Acres",
        nullable=False,
    )

    # ========================================================
    # FARMING SEASON
    # ========================================================

    season: Mapped[FarmingSeason] = mapped_column(
        SqlEnum(
            FarmingSeason,
            name="farming_season",
        ),
        nullable=False,
    )

    # ========================================================
    # FARMING YEAR
    # ========================================================

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # SOWING DATE
    # ========================================================

    sowing_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # ========================================================
    # EXPECTED HARVEST DATE
    #
    # Planned/estimated harvest date.
    #
    # This is NOT the actual harvest date.
    # ========================================================

    expected_harvest_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # ========================================================
    # ACTUAL HARVEST DATE
    #
    # Date on which the crop was actually harvested.
    #
    # NULL while crop is:
    #
    #     PLANNED
    #     ACTIVE
    #
    # Set when:
    #
    #     ACTIVE → HARVESTED
    #
    # ========================================================

    harvested_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # ========================================================
    # STATUS
    #
    # AUTHORITATIVE CROP LIFECYCLE STATE.
    #
    # PLANNED
    # ACTIVE
    # HARVESTED
    # CANCELLED
    #
    # The service layer is responsible for valid state
    # transitions.
    # ========================================================

    status: Mapped[CropSeasonStatus] = mapped_column(
        SqlEnum(
            CropSeasonStatus,
            name="crop_season_status",
        ),
        default=CropSeasonStatus.PLANNED,
        nullable=False,
        index=True,
    )

    # ========================================================
    # ACTIVE FLAG
    #
    # Compatibility field.
    #
    # `status` is authoritative.
    #
    # Expected values:
    #
    # PLANNED    → False
    # ACTIVE     → True
    # HARVESTED  → False
    # CANCELLED  → False
    #
    # The service layer MUST keep this synchronized with
    # `status`.
    # ========================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
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
    # CANCELLATION REASON
    # ========================================================

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # FARM RELATIONSHIP
    # ========================================================

    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="crop_seasons",
    )

    # ========================================================
    # CROP STAGES
    #
    # CropSeason
    #      ↓
    # CropStage
    #
    # Deleting a crop season deletes its stages.
    # ========================================================

    stages: Mapped[list["CropStage"]] = relationship(
        "CropStage",
        back_populates="crop_season",
        cascade="all, delete-orphan",
        order_by="CropStage.stage_order",
    )

    # ========================================================
    # ACTIVITIES
    #
    # CropSeason
    #      ↓
    # Activity
    #
    # An activity may optionally belong to a crop stage.
    #
    # Deleting a crop season deletes its activities.
    # ========================================================

    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="crop_season",
        cascade="all, delete-orphan",
    )