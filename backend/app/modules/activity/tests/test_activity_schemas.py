from datetime import date

import pytest
from pydantic import ValidationError

from app.modules.activity.models import (
    ActivityPriority,
    ActivityType,
)

from app.modules.activity.schemas import (
    ActivityCreateRequest,
    ActivityUpdateRequest,
)


# ============================================================
# VALID CREATE
# ============================================================


def test_valid_create_request():

    request = ActivityCreateRequest(
        activity_type=ActivityType.IRRIGATION,
        title="  Irrigate field  ",
        scheduled_date=date(
            2026,
            8,
            20,
        ),
        priority=ActivityPriority.HIGH,
    )

    assert request.title == "Irrigate field"
    assert request.priority == ActivityPriority.HIGH


# ============================================================
# TITLE TRIMMING
# ============================================================


def test_title_is_trimmed():

    request = ActivityCreateRequest(
        activity_type=ActivityType.IRRIGATION,
        title="   Water field   ",
        scheduled_date=date.today(),
    )

    assert request.title == "Water field"


# ============================================================
# INVALID TITLE
# ============================================================


def test_title_cannot_be_only_spaces():

    with pytest.raises(
        ValidationError,
    ):

        ActivityCreateRequest(
            activity_type=ActivityType.IRRIGATION,
            title="   ",
            scheduled_date=date.today(),
        )


# ============================================================
# DESCRIPTION EMPTY
# ============================================================


def test_empty_description_becomes_none():

    request = ActivityCreateRequest(
        activity_type=ActivityType.IRRIGATION,
        title="Irrigate field",
        description="   ",
        scheduled_date=date.today(),
    )

    assert request.description is None


# ============================================================
# NOTES EMPTY
# ============================================================


def test_empty_notes_becomes_none():

    request = ActivityCreateRequest(
        activity_type=ActivityType.IRRIGATION,
        title="Irrigate field",
        notes="   ",
        scheduled_date=date.today(),
    )

    assert request.notes is None


# ============================================================
# INVALID DURATION
# ============================================================


def test_duration_must_be_positive():

    with pytest.raises(
        ValidationError,
    ):

        ActivityCreateRequest(
            activity_type=ActivityType.IRRIGATION,
            title="Irrigate field",
            scheduled_date=date.today(),
            estimated_duration_minutes=0,
        )


# ============================================================
# UPDATE CAN BE EMPTY
# ============================================================


def test_update_request_can_be_empty():

    request = ActivityUpdateRequest()

    assert request.model_dump(
        exclude_unset=True,
    ) == {}


# ============================================================
# EXPLICIT NULL STAGE
# ============================================================


def test_update_can_explicitly_clear_stage():

    request = ActivityUpdateRequest(
        stage_id=None,
    )

    data = request.model_dump(
        exclude_unset=True,
    )

    assert "stage_id" in data
    assert data["stage_id"] is None


# ============================================================
# UNSUPPORTED FIELD
# ============================================================


def test_update_rejects_status():

    with pytest.raises(
        ValidationError,
    ):

        ActivityUpdateRequest(
            status="COMPLETED",
        )