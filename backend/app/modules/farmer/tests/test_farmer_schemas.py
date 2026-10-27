import pytest
from pydantic import ValidationError

from app.modules.farmer.schemas import (
    FarmerCreateRequest,
    FarmerUpdateRequest,
)


# ============================================================
# CREATE REQUEST
# ============================================================


def test_create_request_valid():

    request = FarmerCreateRequest(
        preferred_language="Telugu",
        experience_years=10,
    )

    assert request.preferred_language == "Telugu"
    assert request.experience_years == 10


def test_create_request_default_language():

    request = FarmerCreateRequest()

    assert request.preferred_language == "English"
    assert request.experience_years is None


def test_create_request_trims_language():

    request = FarmerCreateRequest(
        preferred_language="  Telugu  ",
    )

    assert request.preferred_language == "Telugu"


def test_create_request_rejects_empty_language():

    with pytest.raises(ValidationError):

        FarmerCreateRequest(
            preferred_language="   ",
        )


def test_create_request_rejects_long_language():

    with pytest.raises(ValidationError):

        FarmerCreateRequest(
            preferred_language="A" * 21,
        )


def test_create_request_rejects_negative_experience():

    with pytest.raises(ValidationError):

        FarmerCreateRequest(
            experience_years=-1,
        )


def test_create_request_rejects_experience_above_80():

    with pytest.raises(ValidationError):

        FarmerCreateRequest(
            experience_years=81,
        )


def test_create_request_accepts_zero_experience():

    request = FarmerCreateRequest(
        experience_years=0,
    )

    assert request.experience_years == 0


def test_create_request_accepts_max_experience():

    request = FarmerCreateRequest(
        experience_years=80,
    )

    assert request.experience_years == 80


# ============================================================
# UPDATE REQUEST
# ============================================================


def test_update_request_valid():

    request = FarmerUpdateRequest(
        preferred_language="Hindi",
        experience_years=5,
    )

    assert request.preferred_language == "Hindi"
    assert request.experience_years == 5


def test_update_request_can_be_empty():

    request = FarmerUpdateRequest()

    assert request.model_dump(
        exclude_unset=True,
    ) == {}


def test_update_request_trims_language():

    request = FarmerUpdateRequest(
        preferred_language="  Telugu  ",
    )

    assert request.preferred_language == "Telugu"


def test_update_request_rejects_empty_language():

    with pytest.raises(ValidationError):

        FarmerUpdateRequest(
            preferred_language="   ",
        )


def test_update_request_rejects_negative_experience():

    with pytest.raises(ValidationError):

        FarmerUpdateRequest(
            experience_years=-1,
        )


def test_update_request_rejects_experience_above_80():

    with pytest.raises(ValidationError):

        FarmerUpdateRequest(
            experience_years=81,
        )


# ============================================================
# EXPLICIT NULL
# ============================================================


def test_update_request_can_clear_experience():

    request = FarmerUpdateRequest(
        experience_years=None,
    )

    data = request.model_dump(
        exclude_unset=True,
    )

    assert "experience_years" in data
    assert data["experience_years"] is None