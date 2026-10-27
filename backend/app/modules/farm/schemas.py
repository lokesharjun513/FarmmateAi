from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.shared.constants import LAND_UNIT_ACRES


# ============================================================
# FARM CREATE
# ============================================================


class FarmCreateRequest(BaseModel):

    farm_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

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

    mandal: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    village: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    land_area: float = Field(
        ...,
        gt=0,
    )

    land_unit: str = Field(
        default=LAND_UNIT_ACRES,
        min_length=1,
        max_length=20,
    )

    soil_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    water_source: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    water_availability: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    irrigation_method: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    is_primary: bool = False

    @field_validator(
        "farm_name",
        "state",
        "district",
        "mandal",
        "village",
        "land_unit",
        "soil_type",
        "water_source",
        "water_availability",
        "irrigation_method",
    )
    @classmethod
    def strip_string_fields(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "String value cannot be empty.",
            )

        return value


# ============================================================
# FARM UPDATE
# ============================================================


class FarmUpdateRequest(BaseModel):

    farm_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    mandal: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    village: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    land_area: float | None = Field(
        default=None,
        gt=0,
    )

    land_unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    soil_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    water_source: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    water_availability: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    irrigation_method: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    is_primary: bool | None = None

    @field_validator(
        "farm_name",
        "state",
        "district",
        "mandal",
        "village",
        "land_unit",
        "soil_type",
        "water_source",
        "water_availability",
        "irrigation_method",
    )
    @classmethod
    def strip_string_fields(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "String value cannot be empty.",
            )

        return value


# ============================================================
# FARM RESPONSE
# ============================================================


class FarmResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    farmer_id: UUID

    farm_name: str

    state: str
    district: str
    mandal: str
    village: str

    latitude: float | None
    longitude: float | None

    land_area: float

    land_unit: str

    soil_type: str | None

    water_source: str | None

    water_availability: str | None

    irrigation_method: str | None

    is_primary: bool