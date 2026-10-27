import pytest
from pydantic import ValidationError as PydanticValidationError

from app.modules.crop_planner.schemas import (
    ActivityPriority,
    AIActivity,
    AICropStage,
    CropPlanResponse,
    CropPlanGenerateRequest,
    CropPlanGenerateResponse,
)


# ============================================================
# HELPERS
# ============================================================


def make_activity(
    *,
    day: int = 1,
    title: str = "Irrigate field",
    activity_type: str = "IRRIGATION",
    description: str = "Provide irrigation to the crop.",
    priority: ActivityPriority = ActivityPriority.MEDIUM,
    duration: int = 30,
):
    return AIActivity(
        day=day,
        title=title,
        activity_type=activity_type,
        description=description,
        priority=priority,
        estimated_duration_minutes=duration,
    )


def make_stage(
    *,
    name: str = "Vegetative",
    description: str = "Vegetative growth stage.",
    stage_order: int = 1,
    start_day: int = 1,
    end_day: int = 30,
    activities=None,
):
    return AICropStage(
        name=name,
        description=description,
        stage_order=stage_order,
        start_day=start_day,
        end_day=end_day,
        activities=(
            activities
            if activities is not None
            else [make_activity(day=start_day)]
        ),
    )


def make_plan(
    *,
    crop_name: str = "Rice",
    crop_variety: str | None = "BPT 5204",
    season: str = "KHARIF",
    duration: int = 120,
    stages=None,
):
    if stages is None:
        stages = [
            make_stage(
                stage_order=1,
                start_day=1,
                end_day=30,
            ),
            make_stage(
                name="Flowering",
                description="Flowering stage.",
                stage_order=2,
                start_day=31,
                end_day=60,
                activities=[
                    make_activity(day=31),
                ],
            ),
        ]

    return CropPlanResponse(
        crop_name=crop_name,
        crop_variety=crop_variety,
        season=season,
        estimated_duration_days=duration,
        stages=stages,
    )


# ============================================================
# ACTIVITY PRIORITY
# ============================================================


def test_activity_priority_values():

    assert ActivityPriority.HIGH.value == "HIGH"
    assert ActivityPriority.MEDIUM.value == "MEDIUM"
    assert ActivityPriority.LOW.value == "LOW"


# ============================================================
# AI ACTIVITY - SUCCESS
# ============================================================


def test_ai_activity_valid():

    activity = make_activity()

    assert activity.day == 1
    assert activity.title == "Irrigate field"
    assert activity.activity_type == "IRRIGATION"
    assert activity.priority == ActivityPriority.MEDIUM
    assert activity.estimated_duration_minutes == 30


# ============================================================
# AI ACTIVITY - VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "day",
    [0, -1],
)
def test_ai_activity_day_must_be_at_least_one(day):

    with pytest.raises(PydanticValidationError):

        make_activity(day=day)


@pytest.mark.parametrize(
    "title",
    ["", "A", "x" * 101],
)
def test_ai_activity_title_length(title):

    with pytest.raises(PydanticValidationError):

        make_activity(title=title)


@pytest.mark.parametrize(
    "activity_type",
    ["", "A", "x" * 51],
)
def test_ai_activity_type_length(activity_type):

    with pytest.raises(PydanticValidationError):

        make_activity(
            activity_type=activity_type,
        )


@pytest.mark.parametrize(
    "description",
    ["", "A", "x" * 1001],
)
def test_ai_activity_description_length(description):

    with pytest.raises(PydanticValidationError):

        make_activity(
            description=description,
        )


@pytest.mark.parametrize(
    "duration",
    [0, -1, 1441],
)
def test_ai_activity_duration_range(duration):

    with pytest.raises(PydanticValidationError):

        make_activity(
            duration=duration,
        )


# ============================================================
# AI CROP STAGE - SUCCESS
# ============================================================


def test_ai_crop_stage_valid():

    stage = make_stage()

    assert stage.name == "Vegetative"
    assert stage.stage_order == 1
    assert stage.start_day == 1
    assert stage.end_day == 30
    assert len(stage.activities) == 1


# ============================================================
# AI CROP STAGE - VALIDATION
# ============================================================


def test_ai_crop_stage_end_day_cannot_be_before_start_day():

    with pytest.raises(
        PydanticValidationError,
        match="Stage end day must be greater",
    ):

        make_stage(
            start_day=30,
            end_day=20,
        )


def test_ai_crop_stage_requires_activities():

    with pytest.raises(
        PydanticValidationError,
        match="must contain at least one activity",
    ):

        make_stage(
            activities=[],
        )


def test_ai_crop_stage_activity_before_start_day_fails():

    with pytest.raises(
        PydanticValidationError,
        match="occurs before stage start day",
    ):

        make_stage(
            start_day=10,
            end_day=30,
            activities=[
                make_activity(day=9),
            ],
        )


def test_ai_crop_stage_activity_after_end_day_fails():

    with pytest.raises(
        PydanticValidationError,
        match="occurs after stage end day",
    ):

        make_stage(
            start_day=1,
            end_day=10,
            activities=[
                make_activity(day=11),
            ],
        )


def test_ai_crop_stage_activity_on_start_day_is_valid():

    stage = make_stage(
        start_day=10,
        end_day=20,
        activities=[
            make_activity(day=10),
        ],
    )

    assert stage.activities[0].day == 10


def test_ai_crop_stage_activity_on_end_day_is_valid():

    stage = make_stage(
        start_day=10,
        end_day=20,
        activities=[
            make_activity(day=20),
        ],
    )

    assert stage.activities[0].day == 20


# ============================================================
# CROP PLAN - SUCCESS
# ============================================================


def test_crop_plan_valid():

    plan = make_plan()

    assert plan.crop_name == "Rice"
    assert plan.crop_variety == "BPT 5204"
    assert plan.season == "KHARIF"
    assert plan.estimated_duration_days == 120
    assert len(plan.stages) == 2


def test_crop_plan_allows_missing_crop_variety():

    plan = make_plan(
        crop_variety=None,
    )

    assert plan.crop_variety is None


# ============================================================
# CROP PLAN - BASIC FIELD VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "crop_name",
    ["", "A", "x" * 101],
)
def test_crop_plan_crop_name_length(crop_name):

    with pytest.raises(PydanticValidationError):

        make_plan(
            crop_name=crop_name,
        )


@pytest.mark.parametrize(
    "season",
    ["", "A", "x" * 31],
)
def test_crop_plan_season_length(season):

    with pytest.raises(PydanticValidationError):

        make_plan(
            season=season,
        )


@pytest.mark.parametrize(
    "duration",
    [0, -1, 1001],
)
def test_crop_plan_duration_range(duration):

    with pytest.raises(PydanticValidationError):

        make_plan(
            duration=duration,
        )


# ============================================================
# CROP PLAN - STAGE VALIDATION
# ============================================================


def test_crop_plan_requires_at_least_one_stage():

    with pytest.raises(
        PydanticValidationError,
        match="Crop plan must contain at least one stage",
    ):

        CropPlanResponse(
            crop_name="Rice",
            crop_variety="BPT 5204",
            season="KHARIF",
            estimated_duration_days=120,
            stages=[],
        )


def test_crop_plan_stage_orders_must_be_unique():

    stages = [
        make_stage(
            stage_order=1,
        ),
        make_stage(
            name="Flowering",
            stage_order=1,
            start_day=31,
            end_day=60,
            activities=[
                make_activity(day=31),
            ],
        ),
    ]

    with pytest.raises(
        PydanticValidationError,
        match="Crop stage orders must be unique",
    ):

        make_plan(
            stages=stages,
        )


def test_crop_plan_stage_orders_must_start_at_one():

    stages = [
        make_stage(
            stage_order=2,
        ),
        make_stage(
            name="Flowering",
            stage_order=3,
            start_day=31,
            end_day=60,
            activities=[
                make_activity(day=31),
            ],
        ),
    ]

    with pytest.raises(
        PydanticValidationError,
        match="must start at 1 and be sequential",
    ):

        make_plan(
            stages=stages,
        )


def test_crop_plan_stage_orders_must_be_sequential():

    stages = [
        make_stage(
            stage_order=1,
        ),
        make_stage(
            name="Flowering",
            stage_order=3,
            start_day=31,
            end_day=60,
            activities=[
                make_activity(day=31),
            ],
        ),
    ]

    with pytest.raises(
        PydanticValidationError,
        match="must start at 1 and be sequential",
    ):

        make_plan(
            stages=stages,
        )


def test_crop_plan_stage_cannot_extend_beyond_duration():

    stages = [
        make_stage(
            stage_order=1,
            start_day=1,
            end_day=121,
        ),
    ]

    with pytest.raises(
        PydanticValidationError,
        match="extends beyond crop duration",
    ):

        make_plan(
            duration=120,
            stages=stages,
        )


# ============================================================
# GENERATE REQUEST
# ============================================================


def test_crop_plan_generate_request_valid():

    request = CropPlanGenerateRequest(
        state="Andhra Pradesh",
        district="Nellore",
        village="Vasili",
        soil_type="Clay",
    )

    assert request.state == "Andhra Pradesh"
    assert request.district == "Nellore"
    assert request.village == "Vasili"
    assert request.soil_type == "Clay"


def test_crop_plan_generate_request_soil_type_optional():

    request = CropPlanGenerateRequest(
        state="Andhra Pradesh",
        district="Nellore",
        village="Vasili",
    )

    assert request.soil_type is None


@pytest.mark.parametrize(
    "field",
    [
        "state",
        "district",
        "village",
    ],
)
def test_crop_plan_generate_request_required_fields(
    field,
):

    data = {
        "state": "Andhra Pradesh",
        "district": "Nellore",
        "village": "Vasili",
    }

    del data[field]

    with pytest.raises(PydanticValidationError):

        CropPlanGenerateRequest(**data)


@pytest.mark.parametrize(
    "field",
    [
        "state",
        "district",
        "village",
    ],
)
def test_crop_plan_generate_request_minimum_length(
    field,
):

    data = {
        "state": "Andhra Pradesh",
        "district": "Nellore",
        "village": "Vasili",
    }

    data[field] = "A"

    with pytest.raises(PydanticValidationError):

        CropPlanGenerateRequest(**data)


# ============================================================
# GENERATE RESPONSE
# ============================================================


def test_crop_plan_generate_response_valid():

    from uuid import uuid4

    crop_season_id = uuid4()

    response = CropPlanGenerateResponse(
        crop_season_id=crop_season_id,
        crop_name="Rice",
        crop_variety="BPT 5204",
        season="KHARIF",
        estimated_duration_days=120,
        stages_created=4,
        activities_created=15,
    )

    assert response.crop_season_id == crop_season_id
    assert response.crop_name == "Rice"
    assert response.crop_variety == "BPT 5204"
    assert response.season == "KHARIF"
    assert response.estimated_duration_days == 120
    assert response.stages_created == 4
    assert response.activities_created == 15


def test_crop_plan_generate_response_allows_missing_variety():

    from uuid import uuid4

    response = CropPlanGenerateResponse(
        crop_season_id=uuid4(),
        crop_name="Rice",
        crop_variety=None,
        season="KHARIF",
        estimated_duration_days=120,
        stages_created=4,
        activities_created=15,
    )

    assert response.crop_variety is None


# ============================================================
# EXTRA FIELDS
# ============================================================


def test_ai_activity_allows_extra_fields():

    activity = AIActivity(
        day=1,
        title="Irrigate field",
        activity_type="IRRIGATION",
        description="Provide irrigation.",
        priority="MEDIUM",
        estimated_duration_minutes=30,
        extra_field="ignored",
    )

    assert activity.title == "Irrigate field"


def test_crop_plan_allows_extra_fields():

    plan = make_plan()

    data = plan.model_dump()
    data["extra_field"] = "ignored"

    result = CropPlanResponse.model_validate(data)

    assert result.crop_name == "Rice"