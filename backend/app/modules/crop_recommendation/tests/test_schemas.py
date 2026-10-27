from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.crop_recommendation.schemas import (
    CropRecommendationRequest,
    CropRecommendationResponse,
    RecommendedCrop,
)


def valid_crop():

    return {
        "crop_name": "Rice",
        "confidence": 95,
        "reason": "Suitable for the current season and water conditions.",
    }


def valid_response():

    return {
        "farm_id": str(uuid4()),
        "recommended_sowing_date": "2026-08-20",
        "recommended_crops": [
            valid_crop(),
            {
                "crop_name": "Maize",
                "confidence": 80,
                "reason": "Good alternative for the available conditions.",
            },
            {
                "crop_name": "Groundnut",
                "confidence": 70,
                "reason": "Can be considered under suitable soil conditions.",
            },
        ],
    }


# ============================================================
# REQUEST
# ============================================================


def test_request_valid():

    farm_id = uuid4()

    result = CropRecommendationRequest(
        farm_id=farm_id,
    )

    assert result.farm_id == farm_id


def test_request_requires_farm_id():

    with pytest.raises(ValidationError):

        CropRecommendationRequest()


def test_request_rejects_invalid_uuid():

    with pytest.raises(ValidationError):

        CropRecommendationRequest(
            farm_id="invalid",
        )


# ============================================================
# RECOMMENDED CROP
# ============================================================


def test_recommended_crop_valid():

    result = RecommendedCrop(
        **valid_crop(),
    )

    assert result.crop_name == "Rice"
    assert result.confidence == 95


@pytest.mark.parametrize(
    "confidence",
    [-1, 101],
)
def test_confidence_must_be_between_zero_and_hundred(
    confidence,
):

    with pytest.raises(ValidationError):

        RecommendedCrop(
            crop_name="Rice",
            confidence=confidence,
            reason="Suitable crop.",
        )


@pytest.mark.parametrize(
    "crop_name",
    ["", "x" * 101],
)
def test_crop_name_length(
    crop_name,
):

    with pytest.raises(ValidationError):

        RecommendedCrop(
            crop_name=crop_name,
            confidence=80,
            reason="Suitable crop.",
        )


@pytest.mark.parametrize(
    "reason",
    ["", "x" * 1001],
)
def test_reason_length(
    reason,
):

    with pytest.raises(ValidationError):

        RecommendedCrop(
            crop_name="Rice",
            confidence=80,
            reason=reason,
        )


# ============================================================
# RESPONSE
# ============================================================


def test_response_valid():

    result = CropRecommendationResponse(
        **valid_response(),
    )

    assert result.farm_id
    assert result.recommended_sowing_date == "2026-08-20"
    assert len(result.recommended_crops) == 3


def test_response_requires_farm_id():

    data = valid_response()

    data.pop("farm_id")

    with pytest.raises(ValidationError):

        CropRecommendationResponse(**data)


def test_response_requires_sowing_date():

    data = valid_response()

    data.pop("recommended_sowing_date")

    with pytest.raises(ValidationError):

        CropRecommendationResponse(**data)


def test_response_requires_recommendations():

    data = valid_response()

    data.pop("recommended_crops")

    with pytest.raises(ValidationError):

        CropRecommendationResponse(**data)


def test_response_requires_at_least_one_crop():

    data = valid_response()

    data["recommended_crops"] = []

    with pytest.raises(ValidationError):

        CropRecommendationResponse(**data)