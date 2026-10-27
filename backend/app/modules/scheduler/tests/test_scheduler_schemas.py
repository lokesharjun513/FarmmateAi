import pytest
from pydantic import ValidationError

from app.modules.scheduler.schemas import SchedulerRunResponse


# ============================================================
# VALID RESPONSE
# ============================================================


def test_scheduler_run_response_valid():

    result = SchedulerRunResponse(
        processed_farms=5,
        processed_crop_seasons=4,
        weather_updated=3,
        advisor_generated=4,
        notifications_created=4,
        expired_sessions=2,
        completed=True,
    )

    assert result.processed_farms == 5
    assert result.processed_crop_seasons == 4
    assert result.weather_updated == 3
    assert result.advisor_generated == 4
    assert result.notifications_created == 4
    assert result.expired_sessions == 2
    assert result.completed is True


# ============================================================
# ZERO COUNTS
# ============================================================


def test_scheduler_run_response_accepts_zero_counts():

    result = SchedulerRunResponse(
        processed_farms=0,
        processed_crop_seasons=0,
        weather_updated=0,
        advisor_generated=0,
        notifications_created=0,
        expired_sessions=0,
        completed=True,
    )

    assert result.processed_farms == 0
    assert result.processed_crop_seasons == 0
    assert result.weather_updated == 0
    assert result.advisor_generated == 0
    assert result.notifications_created == 0
    assert result.expired_sessions == 0


# ============================================================
# COMPLETED FALSE
# ============================================================


def test_scheduler_run_response_accepts_completed_false():

    result = SchedulerRunResponse(
        processed_farms=0,
        processed_crop_seasons=0,
        weather_updated=0,
        advisor_generated=0,
        notifications_created=0,
        expired_sessions=0,
        completed=False,
    )

    assert result.completed is False


# ============================================================
# REQUIRED FIELDS
# ============================================================


@pytest.mark.parametrize(
    "field",
    [
        "processed_farms",
        "processed_crop_seasons",
        "weather_updated",
        "advisor_generated",
        "notifications_created",
        "expired_sessions",
        "completed",
    ],
)
def test_scheduler_run_response_requires_all_fields(field):

    data = {
        "processed_farms": 1,
        "processed_crop_seasons": 1,
        "weather_updated": 1,
        "advisor_generated": 1,
        "notifications_created": 1,
        "expired_sessions": 1,
        "completed": True,
    }

    data.pop(field)

    with pytest.raises(ValidationError):

        SchedulerRunResponse(**data)


# ============================================================
# SERIALIZATION
# ============================================================


def test_scheduler_run_response_model_dump():

    result = SchedulerRunResponse(
        processed_farms=5,
        processed_crop_seasons=4,
        weather_updated=3,
        advisor_generated=4,
        notifications_created=4,
        expired_sessions=2,
        completed=True,
    )

    data = result.model_dump()

    assert data == {
        "processed_farms": 5,
        "processed_crop_seasons": 4,
        "weather_updated": 3,
        "advisor_generated": 4,
        "notifications_created": 4,
        "expired_sessions": 2,
        "completed": True,
    }