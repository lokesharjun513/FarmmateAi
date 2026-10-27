from datetime import date

import pytest
from pydantic import ValidationError

from app.modules.activity.models import (
    ActivityPriority,
    ActivityType,
)

from app.modules.crop_plan.schemas import (
    CropPlanActivityRequest,
    CropPlanGenerateRequest,
    CropPlanRegenerateRequest,
    CropPlanStageRequest,
    CropPlanResponse,
    CropPlanStageResponse,
    CropPlanActivityResponse,
)

from app.modules.crop_season.models import (
    CropSeasonStatus,
)


# ============================================================
# HELPERS
# ============================================================


def valid_activity_data():
    return {
        "activity_type": list(ActivityType)[0],
        "title": "Apply fertilizer",
        "description": "Apply recommended fertilizer.",
        "day": 5,
        "priority": ActivityPriority.MEDIUM,
        "estimated_duration_minutes": 30,
    }


def valid_stage_data():
    return {
        "name": "Vegetative Stage",
        "description": "Vegetative growth stage.",
        "stage_order": 1,
        "start_day": 1,
        "end_day": 15,
        "activities": [],
    }


# ============================================================
# CROP PLAN ACTIVITY REQUEST
# ============================================================


def test_activity_request_valid():

    request = CropPlanActivityRequest(
        **valid_activity_data(),
    )

    assert request.title == "Apply fertilizer"
    assert request.day == 5
    assert request.priority == ActivityPriority.MEDIUM
    assert request.estimated_duration_minutes == 30


def test_activity_request_description_is_optional():

    data = valid_activity_data()
    data.pop("description")

    request = CropPlanActivityRequest(**data)

    assert request.description is None


def test_activity_request_duration_is_optional():

    data = valid_activity_data()
    data.pop("estimated_duration_minutes")

    request = CropPlanActivityRequest(**data)

    assert request.estimated_duration_minutes is None


def test_activity_request_default_priority():

    data = valid_activity_data()
    data.pop("priority")

    request = CropPlanActivityRequest(**data)

    assert request.priority == ActivityPriority.MEDIUM


@pytest.mark.parametrize(
    "title",
    [
        "",
        "A",
    ],
)
def test_activity_request_rejects_invalid_title(title):

    data = valid_activity_data()
    data["title"] = title

    with pytest.raises(ValidationError):
        CropPlanActivityRequest(**data)


def test_activity_request_rejects_title_over_100_characters():

    data = valid_activity_data()
    data["title"] = "A" * 101

    with pytest.raises(ValidationError):
        CropPlanActivityRequest(**data)


def test_activity_request_rejects_negative_day():

    data = valid_activity_data()
    data["day"] = -1

    with pytest.raises(ValidationError):
        CropPlanActivityRequest(**data)


def test_activity_request_rejects_zero_day():

    data = valid_activity_data()
    data["day"] = 0

    with pytest.raises(ValidationError):
        CropPlanActivityRequest(**data)


def test_activity_request_rejects_zero_duration():

    data = valid_activity_data()
    data["estimated_duration_minutes"] = 0

    with pytest.raises(ValidationError):
        CropPlanActivityRequest(**data)


def test_activity_request_rejects_negative_duration():

    data = valid_activity_data()
    data["estimated_duration_minutes"] = -10

    with pytest.raises(ValidationError):
        CropPlanActivityRequest(**data)


# ============================================================
# CROP PLAN STAGE REQUEST
# ============================================================


def test_stage_request_valid():

    request = CropPlanStageRequest(
        **valid_stage_data(),
    )

    assert request.name == "Vegetative Stage"
    assert request.stage_order == 1
    assert request.start_day == 1
    assert request.end_day == 15
    assert request.activities == []


def test_stage_request_activities_default_to_empty_list():

    request = CropPlanStageRequest(
        name="Vegetative Stage",
        stage_order=1,
        start_day=1,
        end_day=15,
    )

    assert request.activities == []


def test_stage_request_accepts_activities():

    activity = CropPlanActivityRequest(
        **valid_activity_data(),
    )

    request = CropPlanStageRequest(
        name="Vegetative Stage",
        stage_order=1,
        start_day=1,
        end_day=15,
        activities=[activity],
    )

    assert len(request.activities) == 1
    assert request.activities[0].title == "Apply fertilizer"


@pytest.mark.parametrize(
    "name",
    [
        "",
        "A",
    ],
)
def test_stage_request_rejects_invalid_name(name):

    data = valid_stage_data()
    data["name"] = name

    with pytest.raises(ValidationError):
        CropPlanStageRequest(**data)


def test_stage_request_rejects_name_over_100_characters():

    data = valid_stage_data()
    data["name"] = "A" * 101

    with pytest.raises(ValidationError):
        CropPlanStageRequest(**data)


def test_stage_request_rejects_zero_stage_order():

    data = valid_stage_data()
    data["stage_order"] = 0

    with pytest.raises(ValidationError):
        CropPlanStageRequest(**data)


def test_stage_request_rejects_negative_stage_order():

    data = valid_stage_data()
    data["stage_order"] = -1

    with pytest.raises(ValidationError):
        CropPlanStageRequest(**data)


def test_stage_request_rejects_zero_start_day():

    data = valid_stage_data()
    data["start_day"] = 0

    with pytest.raises(ValidationError):
        CropPlanStageRequest(**data)


def test_stage_request_rejects_zero_end_day():

    data = valid_stage_data()
    data["end_day"] = 0

    with pytest.raises(ValidationError):
        CropPlanStageRequest(**data)


# ============================================================
# GENERATE REQUEST
# ============================================================


def test_generate_request_valid():

    request = CropPlanGenerateRequest(
        start_date=date(2026, 8, 10),
        stages=[
            CropPlanStageRequest(
                **valid_stage_data(),
            ),
        ],
    )

    assert request.start_date == date(2026, 8, 10)
    assert len(request.stages) == 1


def test_generate_request_stages_default_to_empty_list():

    request = CropPlanGenerateRequest(
        start_date=date(2026, 8, 10),
    )

    assert request.stages == []


def test_generate_request_requires_start_date():

    with pytest.raises(ValidationError):
        CropPlanGenerateRequest(
            stages=[],
        )


# ============================================================
# REGENERATE REQUEST
# ============================================================


def test_regenerate_request_valid():

    request = CropPlanRegenerateRequest(
        start_date=date(2026, 8, 10),
        stages=[
            CropPlanStageRequest(
                **valid_stage_data(),
            ),
        ],
    )

    assert request.start_date == date(2026, 8, 10)
    assert len(request.stages) == 1


def test_regenerate_request_inherits_generate_request():

    assert issubclass(
        CropPlanRegenerateRequest,
        CropPlanGenerateRequest,
    )


# ============================================================
# RESPONSE MODELS
# ============================================================


def test_activity_response_accepts_valid_data():

    from uuid import uuid4

    activity = CropPlanActivityResponse(
        id=uuid4(),
        crop_season_id=uuid4(),
        stage_id=uuid4(),
        activity_type=list(ActivityType)[0],
        title="Apply fertilizer",
        description="Fertilizer application",
        scheduled_date=date(2026, 8, 15),
        original_scheduled_date=date(2026, 8, 15),
        priority=ActivityPriority.MEDIUM,
        estimated_duration_minutes=30,
    )

    assert activity.title == "Apply fertilizer"


def test_activity_response_allows_null_stage_id():

    from uuid import uuid4

    activity = CropPlanActivityResponse(
        id=uuid4(),
        crop_season_id=uuid4(),
        stage_id=None,
        activity_type=list(ActivityType)[0],
        title="Water crop",
        description=None,
        scheduled_date=date(2026, 8, 15),
        original_scheduled_date=None,
        priority=ActivityPriority.MEDIUM,
        estimated_duration_minutes=None,
    )

    assert activity.stage_id is None


def test_stage_response_valid():

    from uuid import uuid4

    stage = CropPlanStageResponse(
        id=uuid4(),
        crop_season_id=uuid4(),
        name="Vegetative Stage",
        description=None,
        stage_order=1,
        start_day=1,
        end_day=15,
        activities=[],
    )

    assert stage.stage_order == 1
    assert stage.activities == []


def test_crop_plan_response_valid():

    from uuid import uuid4

    crop_season_id = uuid4()

    response = CropPlanResponse(
        crop_season_id=crop_season_id,
        status=CropSeasonStatus.PLANNED,
        start_date=date(2026, 8, 10),
        stages=[],
        total_stages=0,
        total_activities=0,
    )

    assert response.crop_season_id == crop_season_id
    assert response.status == CropSeasonStatus.PLANNED
    assert response.total_stages == 0
    assert response.total_activities == 0