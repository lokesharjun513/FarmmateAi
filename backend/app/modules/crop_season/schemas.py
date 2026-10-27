from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ============================================================
# CROP SEASON STATUS
# ============================================================


class CropSeasonStatus(str, Enum):

    PLANNED = "PLANNED"

    ACTIVE = "ACTIVE"

    HARVESTED = "HARVESTED"

    CANCELLED = "CANCELLED"


# ============================================================
# FARMING SEASON
# ============================================================


class FarmingSeason(str, Enum):

    KHARIF = "KHARIF"

    RABI = "RABI"

    ZAID = "ZAID"


# ============================================================
# CREATE CROP SEASON
# ============================================================
#
# Creates a crop season in:
#
#     PLANNED
#
# The backend controls:
#
#     status
#     is_active
#     harvested_date
#
# ============================================================


class CropSeasonCreateRequest(BaseModel):

    # ========================================================
    # CROP NAME
    # ========================================================

    crop_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    @field_validator("crop_name")
    @classmethod
    def validate_crop_name(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Crop name must contain at least "
                "2 non-space characters."
            )

        return value

    # ========================================================
    # CROP VARIETY
    # ========================================================

    crop_variety: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    @field_validator("crop_variety")
    @classmethod
    def validate_crop_variety(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value if value else None

    # ========================================================
    # FARMING SEASON
    # ========================================================

    season: FarmingSeason

    # ========================================================
    # FARMING YEAR
    # ========================================================

    year: int = Field(
        ...,
        ge=2000,
        le=2100,
    )

    # ========================================================
    # SOWING DATE
    # ========================================================

    sowing_date: date

    # ========================================================
    # EXPECTED HARVEST DATE
    # ========================================================

    expected_harvest_date: date | None = None

    # ========================================================
    # LAND ALLOCATION
    # ========================================================

    land_area: float = Field(
        ...,
        gt=0,
    )

    land_unit: str = Field(
        default="Acres",
        min_length=1,
        max_length=20,
    )

    @field_validator("land_unit")
    @classmethod
    def validate_land_unit(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Land unit cannot be empty."
            )

        return value

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
    # DATE VALIDATION
    # ========================================================

    @model_validator(mode="after")
    def validate_dates(self):

        if (
            self.expected_harvest_date is not None
            and self.expected_harvest_date < self.sowing_date
        ):
            raise ValueError(
                "Expected harvest date must be greater than "
                "or equal to sowing date."
            )

        return self


# ============================================================
# UPDATE CROP SEASON
# ============================================================
#
# Lifecycle fields are intentionally NOT accepted.
#
# Not accepted:
#
#     status
#     is_active
#     harvested_date
#
# Lifecycle operations use dedicated endpoints.
#
# ============================================================


class CropSeasonUpdateRequest(BaseModel):

    # ========================================================
    # CROP NAME
    # ========================================================

    crop_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    @field_validator("crop_name")
    @classmethod
    def validate_crop_name(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Crop name must contain at least "
                "2 non-space characters."
            )

        return value

    # ========================================================
    # CROP VARIETY
    # ========================================================

    crop_variety: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    @field_validator("crop_variety")
    @classmethod
    def validate_crop_variety(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value if value else None

    # ========================================================
    # FARMING SEASON
    # ========================================================

    season: FarmingSeason | None = None

    # ========================================================
    # FARMING YEAR
    # ========================================================

    year: int | None = Field(
        default=None,
        ge=2000,
        le=2100,
    )

    # ========================================================
    # SOWING DATE
    # ========================================================

    sowing_date: date | None = None

    # ========================================================
    # EXPECTED HARVEST DATE
    # ========================================================

    expected_harvest_date: date | None = None

    # ========================================================
    # LAND ALLOCATION
    # ========================================================

    land_area: float | None = Field(
        default=None,
        gt=0,
    )

    land_unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    @field_validator("land_unit")
    @classmethod
    def validate_land_unit(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Land unit cannot be empty."
            )

        return value

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
    # VALIDATE UPDATE
    #
    # At least one field must be supplied.
    #
    # ========================================================

    @model_validator(mode="after")
    def validate_update(self):

        update_data = self.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise ValueError(
                "At least one field must be provided "
                "to update the crop season."
            )

        # ----------------------------------------------------
        # Validate dates when both are supplied.
        # ----------------------------------------------------

        if (
            self.sowing_date is not None
            and self.expected_harvest_date is not None
            and self.expected_harvest_date < self.sowing_date
        ):
            raise ValueError(
                "Expected harvest date must be greater than "
                "or equal to sowing date."
            )

        return self


# ============================================================
# START CROP SEASON REQUEST
# ============================================================
#
# PLANNED
#    ↓
# ACTIVE
#
# No body is currently required.
#
# The schema exists so the API can evolve later without
# changing the endpoint contract.
#
# ============================================================


class CropSeasonStartRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )


# ============================================================
# HARVEST CROP SEASON REQUEST
# ============================================================
#
# ACTIVE
#    ↓
# HARVESTED
#
# harvested_date is optional.
#
# If not supplied, the service uses today's date.
#
# ============================================================


class CropSeasonHarvestRequest(BaseModel):

    harvested_date: date | None = None

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


# ============================================================
# CANCEL CROP SEASON REQUEST
# ============================================================
#
# PLANNED / ACTIVE
#       ↓
#   CANCELLED
#
# Optional reason can be recorded.
#
# ============================================================


class CropSeasonCancelRequest(BaseModel):

    reason: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        return value if value else None


# ============================================================
# CROP SEASON RESPONSE
# ============================================================
#
# Complete representation returned to clients.
#
# ============================================================


class CropSeasonResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ========================================================
    # IDENTITY
    # ========================================================

    id: UUID

    farm_id: UUID

    # ========================================================
    # CROP INFORMATION
    # ========================================================

    crop_name: str

    crop_variety: str | None

    # ========================================================
    # FARMING SEASON
    # ========================================================

    season: FarmingSeason

    year: int

    # ========================================================
    # CROP TIMELINE
    # ========================================================

    sowing_date: date

    expected_harvest_date: date | None

    harvested_date: date | None

    # ========================================================
    # LAND ALLOCATION
    # ========================================================

    land_area: float

    land_unit: str

    # ========================================================
    # LIFECYCLE
    # ========================================================

    status: CropSeasonStatus

    is_active: bool

    # ========================================================
    # ADDITIONAL INFORMATION
    # ========================================================

    notes: str | None

    cancellation_reason: str | None = None