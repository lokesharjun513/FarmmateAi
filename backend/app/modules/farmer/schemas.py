from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# FARMER CREATE
# ============================================================


class FarmerCreateRequest(BaseModel):

    preferred_language: str = Field(
        default="English",
        min_length=1,
        max_length=20,
    )

    experience_years: int | None = Field(
        default=None,
        ge=0,
        le=80,
    )

    @field_validator("preferred_language")
    @classmethod
    def validate_preferred_language(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Preferred language cannot be empty.",
            )

        return value


# ============================================================
# FARMER UPDATE
# ============================================================


class FarmerUpdateRequest(BaseModel):

    preferred_language: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    experience_years: int | None = Field(
        default=None,
        ge=0,
        le=80,
    )

    @field_validator("preferred_language")
    @classmethod
    def validate_preferred_language(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Preferred language cannot be empty.",
            )

        return value


# ============================================================
# FARMER RESPONSE
# ============================================================


class FarmerResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    user_id: UUID

    preferred_language: str

    experience_years: int | None

    profile_completion: int = Field(
        ge=0,
        le=100,
    )

    onboarding_completed: bool