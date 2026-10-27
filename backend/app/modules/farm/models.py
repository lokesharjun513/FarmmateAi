import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    String,
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

    from app.modules.farmer.models import Farmer
    from app.modules.crop_season.models import CropSeason


# ============================================================
# FARM
#
# Represents a physical farm owned by a farmer.
#
# Farmer
#   ├── Farm 1
#   │     └── Crop Seasons
#   │
#   ├── Farm 2
#   │     └── Crop Seasons
#   │
#   └── Farm 3
#         └── Crop Seasons
#
# A farmer can have multiple farms.
# Each farm belongs to exactly one farmer.
# ============================================================


class Farm(Base, TimestampMixin):

    __tablename__ = "farms"

    # ========================================================
    # TABLE CONSTRAINTS
    # ========================================================

    __table_args__ = (

        # ----------------------------------------------------
        # Land area must always be positive.
        # ----------------------------------------------------

        CheckConstraint(
            "land_area > 0",
            name="ck_farm_land_area_positive",
        ),

        # ----------------------------------------------------
        # Latitude must be within the valid geographic range.
        #
        # NULL is allowed when GPS coordinates are not provided.
        # ----------------------------------------------------

        CheckConstraint(
            "latitude IS NULL "
            "OR latitude >= -90 "
            "AND latitude <= 90",
            name="ck_farm_latitude_valid",
        ),

        # ----------------------------------------------------
        # Longitude must be within the valid geographic range.
        #
        # NULL is allowed when GPS coordinates are not provided.
        # ----------------------------------------------------

        CheckConstraint(
            "longitude IS NULL "
            "OR longitude >= -180 "
            "AND longitude <= 180",
            name="ck_farm_longitude_valid",
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
    # FARMER
    #
    # Every farm must belong to a farmer.
    #
    # Deleting the farmer deletes the farm.
    # ========================================================

    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farmers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # FARM INFORMATION
    # ========================================================

    farm_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ========================================================
    # LOCATION
    # ========================================================

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    mandal: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    village: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ========================================================
    # GPS LOCATION
    #
    # Optional because the farmer may manually provide the
    # location without GPS coordinates.
    # ========================================================

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ========================================================
    # LAND INFORMATION
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
    # SOIL INFORMATION
    # ========================================================

    soil_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ========================================================
    # WATER SOURCE
    #
    # Examples:
    #
    # Borewell
    # Canal
    # River
    # Tank
    # Rain-fed
    # ========================================================

    water_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ========================================================
    # WATER AVAILABILITY
    #
    # Examples:
    #
    # LOW
    # MEDIUM
    # HIGH
    # RAIN_FED
    # ========================================================

    water_availability: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # ========================================================
    # IRRIGATION METHOD
    #
    # Examples:
    #
    # Drip
    # Sprinkler
    # Flood
    # Manual
    # Rain-fed
    # ========================================================

    irrigation_method: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # ========================================================
    # PRIMARY FARM
    #
    # True:
    #     This is the farmer's primary/default farm.
    #
    # False:
    #     Secondary farm.
    #
    # IMPORTANT:
    #
    # The one-primary-farm business rule is handled by the
    # FarmRepository.
    #
    # We intentionally do NOT use a database unique index here
    # because the repository must be able to safely transition
    # the primary farm from one farm to another.
    # ========================================================

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ========================================================
    # FARMER RELATIONSHIP
    # ========================================================

    farmer: Mapped["Farmer"] = relationship(
        "Farmer",
        back_populates="farms",
    )

    # ========================================================
    # CROP SEASONS
    #
    # One farm can have multiple crop seasons over time.
    #
    # Farm
    #   ├── Rice 2025
    #   ├── Rice 2026
    #   ├── Black Gram 2026
    #   └── Maize 2027
    #
    # Deleting a farm deletes its crop seasons.
    # ========================================================

    crop_seasons: Mapped[list["CropSeason"]] = relationship(
        "CropSeason",
        back_populates="farm",
        cascade="all, delete-orphan",
    )