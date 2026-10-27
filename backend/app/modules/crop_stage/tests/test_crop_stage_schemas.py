import pytest
from pydantic import ValidationError

from app.modules.crop_stage.models import CropStageStatus
from app.modules.crop_stage.schemas import (
    CropStageCreateRequest,
    CropStageUpdateRequest,
)


# ============================================================
# CREATE REQUEST
# ============================================================


def test_valid_create_request():

    request = CropStageCreateRequest(
        name="Land Preparation",
        description="Prepare the field.",
        stage_order=1,
        start_day=1,
        end_day=10,
    )

    assert request.name == "Land Preparation"
    assert request.stage_order == 1
    assert request.start_day == 1
    assert request.end_day == 10


def test_create_request_requires_name():

    with pytest.raises(ValidationError):
        CropStageCreateRequest(
            stage_order=1,
            start_day=1,
            end_day=10,
        )


def test_create_request_name_min_length():

    with pytest.raises(ValidationError):
        CropStageCreateRequest(
            name="A",
            stage_order=1,
            start_day=1,
            end_day=10,
        )


def test_create_request_stage_order_must_be_positive():

    with pytest.raises(ValidationError):
        CropStageCreateRequest(
            name="Land Preparation",
            stage_order=0,
            start_day=1,
            end_day=10,
        )


def test_create_request_start_day_must_be_positive():

    with pytest.raises(ValidationError):
        CropStageCreateRequest(
            name="Land Preparation",
            stage_order=1,
            start_day=0,
            end_day=10,
        )


def test_create_request_end_day_must_be_positive():

    with pytest.raises(ValidationError):
        CropStageCreateRequest(
            name="Land Preparation",
            stage_order=1,
            start_day=1,
            end_day=0,
        )


def test_create_request_end_day_cannot_be_before_start_day():

    with pytest.raises(
        ValidationError,
        match="End day must be greater than or equal to start day",
    ):
        CropStageCreateRequest(
            name="Land Preparation",
            stage_order=1,
            start_day=10,
            end_day=5,
        )


# ============================================================
# UPDATE REQUEST
# ============================================================


def test_empty_update_request_is_valid():

    request = CropStageUpdateRequest()

    assert request.model_dump(exclude_unset=True) == {}


def test_update_request_valid():

    request = CropStageUpdateRequest(
        name="Updated Stage",
        description="Updated description",
        start_day=5,
        end_day=15,
    )

    assert request.name == "Updated Stage"
    assert request.start_day == 5
    assert request.end_day == 15


def test_update_request_validates_timeline():

    with pytest.raises(
        ValidationError,
        match="End day must be greater than or equal to start day",
    ):
        CropStageUpdateRequest(
            start_day=20,
            end_day=10,
        )


def test_update_request_stage_order_must_be_positive():

    with pytest.raises(ValidationError):
        CropStageUpdateRequest(
            stage_order=0,
        )


# ============================================================
# LIFECYCLE FIELDS MUST NOT BE CLIENT CONTROLLED
# ============================================================


def test_create_request_does_not_accept_status_as_model_field():

    request = CropStageCreateRequest(
        name="Land Preparation",
        stage_order=1,
        start_day=1,
        end_day=10,
    )

    assert "status" not in type(request).model_fields


def test_update_request_does_not_accept_status_as_model_field():

    request = CropStageUpdateRequest(
        name="Updated",
    )

    assert "status" not in type(request).model_fields


def test_update_request_does_not_accept_started_at():

    request = CropStageUpdateRequest(
        name="Updated",
    )

    assert "started_at" not in type(request).model_fields


def test_update_request_does_not_accept_completed_at():

    request = CropStageUpdateRequest(
        name="Updated",
    )

    assert "completed_at" not in type(request).model_fields


# ============================================================
# RESPONSE
# ============================================================


def test_crop_stage_status_values():

    assert CropStageStatus.PENDING.value == "PENDING"
    assert CropStageStatus.ACTIVE.value == "ACTIVE"
    assert CropStageStatus.COMPLETED.value == "COMPLETED"
    assert CropStageStatus.SKIPPED.value == "SKIPPED"