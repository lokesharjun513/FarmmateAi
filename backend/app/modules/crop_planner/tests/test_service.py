import uuid

from datetime import date

import pytest

from app.modules.activity.models import (
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
    ActivityType,
)

from app.modules.crop_planner.schemas import (
    ActivityPriority as AIActivityPriority,
    AIActivity,
    AICropStage,
    CropPlanResponse,
)

from app.modules.crop_planner.service import (
    CropPlannerService,
)

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
    FarmingSeason,
)

from app.shared.exceptions import (
    ValidationError,
)


# ============================================================
# FAKE REPOSITORY
# ============================================================


class FakeCropPlannerRepository:

    def __init__(
        self,
        has_existing_plan=False,
    ):

        self._has_existing_plan = (
            has_existing_plan
        )

        self.created_stages = []

        self.created_activities = []

        self.locked_crop_ids = []

        self.has_plan_results = []

        self.commit_called = False

        self.rollback_called = False

    # --------------------------------------------------------
    # LOCK CROP SEASON
    # --------------------------------------------------------

    def lock_crop_season(
        self,
        crop_season_id,
    ):

        self.locked_crop_ids.append(
            crop_season_id,
        )

    # --------------------------------------------------------
    # PLAN EXISTS
    # --------------------------------------------------------

    def has_plan(
        self,
        crop_season_id,
    ):

        if self.has_plan_results:

            return self.has_plan_results.pop(0)

        return self._has_existing_plan

    # --------------------------------------------------------
    # CREATE STAGE
    # --------------------------------------------------------

    def create_stage(
        self,
        stage,
    ):

        if stage.id is None:
            stage.id = uuid.uuid4()

        self.created_stages.append(
            stage,
        )

        return stage

    # --------------------------------------------------------
    # CREATE ACTIVITIES
    # --------------------------------------------------------

    def create_activities(
        self,
        activities,
    ):

        self.created_activities.extend(
            activities,
        )

        return activities

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------

    def commit(self):

        self.commit_called = True

    # --------------------------------------------------------
    # ROLLBACK
    # --------------------------------------------------------

    def rollback(self):

        self.rollback_called = True


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def crop_season():

    return CropSeason(
        id=uuid.uuid4(),

        farm_id=uuid.uuid4(),

        crop_name="Rice",

        crop_variety="BPT 5204",

        land_area=1.0,

        land_unit="Acres",

        season=FarmingSeason.KHARIF,

        year=2026,

        sowing_date=date(
            2026,
            8,
            1,
        ),

        expected_harvest_date=None,

        harvested_date=None,

        status=CropSeasonStatus.PLANNED,

        is_active=False,

        notes=None,
    )


@pytest.fixture
def valid_plan():

    return CropPlanResponse(

        crop_name="Rice",

        crop_variety="BPT 5204",

        season="KHARIF",

        estimated_duration_days=120,

        stages=[

            AICropStage(

                name="Land Preparation",

                description=(
                    "Prepare the field for rice cultivation."
                ),

                stage_order=1,

                start_day=1,

                end_day=10,

                activities=[

                    AIActivity(

                        day=2,

                        title="Prepare field",

                        activity_type=(
                            "LAND_PREPARATION"
                        ),

                        description=(
                            "Prepare the field before sowing."
                        ),

                        priority=AIActivityPriority.HIGH,

                        estimated_duration_minutes=120,
                    ),

                    AIActivity(

                        day=5,

                        title="Irrigate field",

                        activity_type=(
                            "IRRIGATION"
                        ),

                        description=(
                            "Maintain adequate soil moisture."
                        ),

                        priority=AIActivityPriority.MEDIUM,

                        estimated_duration_minutes=60,
                    ),
                ],
            ),

            AICropStage(

                name="Sowing",

                description=(
                    "Complete rice sowing activities."
                ),

                stage_order=2,

                start_day=11,

                end_day=20,

                activities=[

                    AIActivity(

                        day=12,

                        title="Sow rice",

                        activity_type="SOWING",

                        description=(
                            "Sow the selected rice variety."
                        ),

                        priority=AIActivityPriority.HIGH,

                        estimated_duration_minutes=90,
                    ),
                ],
            ),
        ],
    )


# ============================================================
# SERVICE FIXTURE
# ============================================================


@pytest.fixture
def repository():

    return FakeCropPlannerRepository()


@pytest.fixture
def service(
    repository,
):

    return CropPlannerService(
        repository=repository,
    )


# ============================================================
# MOCK AI
# ============================================================


async def mock_generate(
    self,
    **kwargs,
):

    return kwargs["mock_plan"]


# ============================================================
# GENERATE PLAN - SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_success(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    async def generate(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    result = await service.generate_plan(

        crop_season=crop_season,

        state="Andhra Pradesh",

        district="Nellore",

        village="Sarojinidevi",

        soil_type="Clay",
    )

    assert result == valid_plan

    assert repository.commit_called is True

    assert repository.rollback_called is False

    assert repository.locked_crop_ids == [
        crop_season.id,
    ]

    assert len(
        repository.created_stages
    ) == 2

    assert len(
        repository.created_activities
    ) == 3


# ============================================================
# PLANNER RECEIVES CORRECT PARAMETERS
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_passes_correct_parameters_to_planner(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    captured = {}

    async def generate(
        self,
        **kwargs,
    ):

        captured.update(
            kwargs,
        )

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    await service.generate_plan(

        crop_season=crop_season,

        state="Andhra Pradesh",

        district="Nellore",

        village="Sarojinidevi",

        soil_type="Clay",
    )

    assert captured["crop_name"] == "Rice"

    assert captured["crop_variety"] == "BPT 5204"

    assert captured["season"] == "KHARIF"

    assert captured["state"] == "Andhra Pradesh"

    assert captured["district"] == "Nellore"

    assert captured["village"] == "Sarojinidevi"

    assert captured["land_area"] == 1.0

    assert captured["land_unit"] == "Acres"

    assert captured["soil_type"] == "Clay"


# ============================================================
# CROP SEASON STATUS
# ============================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        CropSeasonStatus.ACTIVE,
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ],
)
async def test_generate_plan_requires_planned_status(
    service,
    repository,
    crop_season,
    valid_plan,
    status,
):

    crop_season.status = status

    with pytest.raises(
        ValidationError,
        match=(
            "Crop plan can only be generated "
            "for a planned crop season."
        ),
    ):

        await service.generate_plan(

            crop_season=crop_season,

            state="Andhra Pradesh",

            district="Nellore",

            village="Sarojinidevi",

            soil_type=None,
        )

    assert repository.commit_called is False


# ============================================================
# DUPLICATE PLAN
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_rejects_duplicate_plan(
    service,
    repository,
    crop_season,
):

    repository._has_existing_plan = True

    with pytest.raises(
        ValidationError,
        match=(
            "A crop plan already exists for "
            "this crop season."
        ),
    ):

        await service.generate_plan(

            crop_season=crop_season,

            state="Andhra Pradesh",

            district="Nellore",

            village="Sarojinidevi",

            soil_type=None,
        )

    assert repository.commit_called is False


@pytest.mark.asyncio
async def test_generate_plan_rechecks_after_lock_to_prevent_duplicates(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    async def generate(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    repository.has_plan_results = [False, True]

    with pytest.raises(
        ValidationError,
        match=(
            "A crop plan already exists for "
            "this crop season."
        ),
    ):

        await service.generate_plan(

            crop_season=crop_season,

            state="Andhra Pradesh",

            district="Nellore",

            village="Sarojinidevi",

            soil_type=None,
        )

    assert repository.locked_crop_ids == [
        crop_season.id,
    ]

    assert repository.created_stages == []

    assert repository.created_activities == []

    assert repository.commit_called is False


# ============================================================
# CROP NAME VALIDATION
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_rejects_different_crop(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    valid_plan.crop_name = "Cotton"

    async def generate(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "AI returned a plan for a different crop."
        ),
    ):

        await service.generate_plan(

            crop_season=crop_season,

            state="Andhra Pradesh",

            district="Nellore",

            village="Sarojinidevi",

            soil_type=None,
        )

    assert repository.commit_called is False


# ============================================================
# CROP VARIETY VALIDATION
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_rejects_different_crop_variety(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    valid_plan.crop_variety = "IR64"

    async def generate(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "AI returned a plan for a different "
            "crop variety."
        ),
    ):

        await service.generate_plan(

            crop_season=crop_season,

            state="Andhra Pradesh",

            district="Nellore",

            village="Sarojinidevi",

            soil_type=None,
        )


# ============================================================
# SEASON VALIDATION
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_rejects_different_season(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    valid_plan.season = "RABI"

    async def generate(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "AI returned a plan for a different "
            "farming season."
        ),
    ):

        await service.generate_plan(

            crop_season=crop_season,

            state="Andhra Pradesh",

            district="Nellore",

            village="Sarojinidevi",

            soil_type=None,
        )


# ============================================================
# STAGE ORDER VALIDATION
# ============================================================


def test_validate_plan_rejects_duplicate_stage_orders(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.stages[1].stage_order = 1

    with pytest.raises(
        ValidationError,
        match=(
            "AI returned duplicate crop stage orders."
        ),
    ):

        service._validate_plan(
            plan=valid_plan,
            crop_season=crop_season,
        )


def test_validate_plan_rejects_non_sequential_stage_orders(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.stages[1].stage_order = 3

    with pytest.raises(
        ValidationError,
        match=(
            "Crop stage orders must be sequential "
            "starting from 1."
        ),
    ):

        service._validate_plan(
            plan=valid_plan,
            crop_season=crop_season,
        )


# ============================================================
# STAGE TIMELINE VALIDATION
# ============================================================


def test_validate_plan_rejects_stage_beyond_duration(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.stages[0].end_day = 121

    with pytest.raises(
        ValidationError,
        match=(
            "Stage 'Land Preparation' extends "
            "beyond crop duration."
        ),
    ):

        service._validate_plan(
            plan=valid_plan,
            crop_season=crop_season,
        )


def test_validate_plan_rejects_activity_outside_stage(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.stages[0].activities[0].day = 11

    with pytest.raises(
        ValidationError,
        match=(
            "Activity 'Prepare field' "
            "is outside its stage timeline."
        ),
    ):

        service._validate_plan(
            plan=valid_plan,
            crop_season=crop_season,
        )


# ============================================================
# ACTIVITY TYPE VALIDATION
# ============================================================


def test_validate_plan_rejects_invalid_activity_type(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.stages[0].activities[0].activity_type = (
        "INVALID_ACTIVITY"
    )

    with pytest.raises(
        ValidationError,
        match="Invalid activity type",
    ):

        service._validate_plan(
            plan=valid_plan,
            crop_season=crop_season,
        )


# ============================================================
# SAVE PLAN - STAGES
# ============================================================


def test_save_plan_creates_stages_in_order(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    assert len(
        repository.created_stages
    ) == 2

    assert (
        repository.created_stages[0].stage_order
        == 1
    )

    assert (
        repository.created_stages[1].stage_order
        == 2
    )


# ============================================================
# SAVE PLAN - STAGE STATUS
# ============================================================


def test_save_plan_creates_pending_stages(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    for stage in repository.created_stages:

        assert (
            stage.status.value
            == "PENDING"
        )


# ============================================================
# SAVE PLAN - ACTIVITIES
# ============================================================


def test_save_plan_creates_activities(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    assert len(
        repository.created_activities
    ) == 3


# ============================================================
# ACTIVITY CROP SEASON
# ============================================================


def test_save_plan_sets_activity_crop_season(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    for activity in repository.created_activities:

        assert (
            activity.crop_season_id
            == crop_season.id
        )


# ============================================================
# ACTIVITY STAGE
# ============================================================


def test_save_plan_assigns_correct_stage(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    first_stage = (
        repository.created_stages[0]
    )

    second_stage = (
        repository.created_stages[1]
    )

    assert (
        repository.created_activities[0].stage_id
        == first_stage.id
    )

    assert (
        repository.created_activities[1].stage_id
        == first_stage.id
    )

    assert (
        repository.created_activities[2].stage_id
        == second_stage.id
    )


# ============================================================
# SCHEDULED DATE
# ============================================================


def test_save_plan_calculates_scheduled_dates(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    activities = (
        repository.created_activities
    )

    assert (
        activities[0].scheduled_date
        == date(2026, 8, 2)
    )

    assert (
        activities[1].scheduled_date
        == date(2026, 8, 5)
    )

    assert (
        activities[2].scheduled_date
        == date(2026, 8, 12)
    )


# ============================================================
# ORIGINAL SCHEDULED DATE
# ============================================================


def test_save_plan_original_scheduled_date_is_none(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    for activity in repository.created_activities:

        assert (
            activity.original_scheduled_date
            is None
        )


# ============================================================
# ACTIVITY STATUS
# ============================================================


def test_save_plan_creates_pending_activities(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    for activity in repository.created_activities:

        assert (
            activity.status
            == ActivityStatus.PENDING
        )


# ============================================================
# ACTIVITY SOURCE
# ============================================================


def test_save_plan_marks_source_as_ai_planned(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    for activity in repository.created_activities:

        assert (
            activity.source
            == ActivitySource.AI_PLANNED
        )


# ============================================================
# ACTIVITY TYPE
# ============================================================


def test_save_plan_converts_activity_type_to_enum(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    assert (
        repository.created_activities[0].activity_type
        == ActivityType.LAND_PREPARATION
    )

    assert (
        repository.created_activities[1].activity_type
        == ActivityType.IRRIGATION
    )

    assert (
        repository.created_activities[2].activity_type
        == ActivityType.SOWING
    )


# ============================================================
# ACTIVITY PRIORITY
# ============================================================


def test_save_plan_preserves_activity_priority(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    assert (
        repository.created_activities[0].priority
        == ActivityPriority.HIGH.value
    )

    assert (
        repository.created_activities[1].priority
        == ActivityPriority.MEDIUM.value
    )


# ============================================================
# ACTIVITY DURATION
# ============================================================


def test_save_plan_preserves_activity_duration(
    service,
    repository,
    crop_season,
    valid_plan,
):

    service._save_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )

    assert (
        repository.created_activities[0]
        .estimated_duration_minutes
        == 120
    )

    assert (
        repository.created_activities[1]
        .estimated_duration_minutes
        == 60
    )


# ============================================================
# SAVE PLAN COUNTS
# ============================================================


def test_save_plan_returns_correct_counts(
    service,
    repository,
    crop_season,
    valid_plan,
):

    stages_created, activities_created = (
        service._save_plan(
            plan=valid_plan,
            crop_season=crop_season,
        )
    )

    assert stages_created == 2

    assert activities_created == 3


# ============================================================
# COMMIT FAILURE
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_rolls_back_when_save_fails(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    async def generate(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    def failing_save(
        **kwargs,
    ):

        raise RuntimeError(
            "Database failure"
        )

    monkeypatch.setattr(
        service,
        "_save_plan",
        failing_save,
    )

    with pytest.raises(
        RuntimeError,
        match="Database failure",
    ):

        await service.generate_plan(

            crop_season=crop_season,

            state="Andhra Pradesh",

            district="Nellore",

            village="Sarojinidevi",

            soil_type=None,
        )

    assert repository.commit_called is False

    assert repository.rollback_called is True


# ============================================================
# COMMIT SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_commits_after_success(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    async def generate(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    await service.generate_plan(

        crop_season=crop_season,

        state="Andhra Pradesh",

        district="Nellore",

        village="Sarojinidevi",

        soil_type=None,
    )

    assert repository.commit_called is True

    assert repository.rollback_called is False


# ============================================================
# OPTIONAL SOIL TYPE
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_allows_missing_soil_type(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    captured = {}

    async def generate(
        self,
        **kwargs,
    ):

        captured.update(
            kwargs,
        )

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    await service.generate_plan(

        crop_season=crop_season,

        state="Andhra Pradesh",

        district="Nellore",

        village="Sarojinidevi",

        soil_type=None,
    )

    assert captured["soil_type"] is None


# ============================================================
# CASE-INSENSITIVE CROP NAME
# ============================================================


def test_validate_plan_crop_name_is_case_insensitive(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.crop_name = "rice"

    service._validate_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )


# ============================================================
# CASE-INSENSITIVE VARIETY
# ============================================================


def test_validate_plan_crop_variety_is_case_insensitive(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.crop_variety = "bpt 5204"

    service._validate_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )


# ============================================================
# CASE-INSENSITIVE SEASON
# ============================================================


def test_validate_plan_season_is_case_insensitive(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.season = "kharif"

    service._validate_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )
# ============================================================
# BOUNDED RETRY AND CANONICAL CROP IDENTITY
# ============================================================


@pytest.mark.asyncio
async def test_generate_plan_retries_name_mismatch_then_succeeds(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    crop_season.crop_name = "Paddy"
    crop_season.crop_variety = None

    wrong_plan = valid_plan.model_copy(deep=True)
    wrong_plan.crop_name = "Rice"
    wrong_plan.crop_variety = None

    correct_plan = valid_plan.model_copy(deep=True)
    correct_plan.crop_name = "Paddy"
    correct_plan.crop_variety = None

    responses = [wrong_plan, correct_plan]
    calls = []

    async def generate(
        self,
        **kwargs,
    ):

        calls.append(kwargs)

        return responses.pop(0)

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    result = await service.generate_plan(
        crop_season=crop_season,
        state="Andhra Pradesh",
        district="Nellore",
        village="Sarojinidevi",
        soil_type=None,
    )

    assert len(calls) == 2
    assert result.crop_name == "Paddy"
    assert result.crop_variety is None
    assert repository.commit_called is True


@pytest.mark.asyncio
async def test_generate_plan_rejects_paddy_rice_after_retry(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    crop_season.crop_name = "Paddy"
    crop_season.crop_variety = None

    wrong_plan = valid_plan.model_copy(deep=True)
    wrong_plan.crop_name = "Rice"
    wrong_plan.crop_variety = None

    calls = 0

    async def generate(
        self,
        **kwargs,
    ):

        nonlocal calls
        calls += 1

        return wrong_plan.model_copy(deep=True)

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "AI could not produce a valid crop plan after "
            "2 attempts"
        ),
    ):

        await service.generate_plan(
            crop_season=crop_season,
            state="Andhra Pradesh",
            district="Nellore",
            village="Sarojinidevi",
            soil_type=None,
        )

    assert calls == 2
    assert repository.commit_called is False


def test_validate_plan_accepts_case_and_whitespace_name(
    service,
    crop_season,
    valid_plan,
):

    crop_season.crop_name = "Paddy"
    valid_plan.crop_name = "  pAdDy  "

    service._validate_plan(
        plan=valid_plan,
        crop_season=crop_season,
    )


def test_validate_plan_rejects_missing_saved_variety(
    service,
    crop_season,
    valid_plan,
):

    valid_plan.crop_variety = None

    with pytest.raises(
        ValidationError,
        match="different crop variety",
    ):

        service._validate_plan(
            plan=valid_plan,
            crop_season=crop_season,
        )


@pytest.mark.asyncio
async def test_generate_plan_retries_invalid_output_then_succeeds(
    monkeypatch,
    service,
    repository,
    crop_season,
    valid_plan,
):

    calls = 0

    async def generate(
        self,
        **kwargs,
    ):

        nonlocal calls
        calls += 1

        if calls == 1:
            raise ValidationError(
                "AI returned invalid JSON."
            )

        return valid_plan

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    result = await service.generate_plan(
        crop_season=crop_season,
        state="Andhra Pradesh",
        district="Nellore",
        village="Sarojinidevi",
        soil_type=None,
    )

    assert calls == 2
    assert result == valid_plan
    assert repository.commit_called is True


@pytest.mark.asyncio
async def test_generate_plan_retry_exhaustion_does_not_commit(
    monkeypatch,
    service,
    repository,
    crop_season,
):

    calls = 0

    async def generate(
        self,
        **kwargs,
    ):

        nonlocal calls
        calls += 1

        raise ValidationError(
            "AI returned invalid JSON."
        )

    monkeypatch.setattr(
        type(service.planner),
        "generate",
        generate,
    )

    with pytest.raises(
        ValidationError,
        match="AI returned invalid JSON.",
    ):

        await service.generate_plan(
            crop_season=crop_season,
            state="Andhra Pradesh",
            district="Nellore",
            village="Sarojinidevi",
            soil_type=None,
        )

    assert calls == 2
    assert repository.commit_called is False
