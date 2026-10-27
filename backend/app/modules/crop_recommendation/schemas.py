from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# CROP RECOMMENDATION REQUEST
# ============================================================


class CropRecommendationRequest(BaseModel):
    """
    Request an AI-based crop recommendation for a farm.

    The backend uses farm_id to load the farm's conditions.
    """

    farm_id: UUID


# ============================================================
# RECOMMENDED CROP
# ============================================================


class RecommendedCrop(BaseModel):

    crop_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    confidence: int = Field(
        ...,
        ge=0,
        le=100,
    )

    reason: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )


# ============================================================
# CROP RECOMMENDATION RESPONSE
# ============================================================


class CropRecommendationResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    farm_id: UUID

    recommended_sowing_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
    )

    recommended_crops: list[RecommendedCrop] = Field(
        ...,
        min_length=1,
    )