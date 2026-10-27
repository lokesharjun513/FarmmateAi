from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.modules.activity.models import (
    Activity,
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
    ActivityType,
)

from app.modules.crop_plan import service

from app.modules.crop_plan.schemas import (
    CropPlanActivityRequest,
    CropPlanGenerateRequest,
    CropPlanStageRequest,
)

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)

from app.shared.exceptions import ValidationError


# ============================================================
# TEST HELPERS
# ============================================================


def make_crop():
    """
    Create a minimal CropSeason object.
    """

    crop = CropSeason(
        id=uuid4(),
        sowing_date=date(
            2026,
            8,
            10,
        ),
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    return crop


def make_activity_request(
    day=2,
    title="Prepare field",
    activity_type=ActivityType.LAND_PREPARATION,
    description="Activity description",
    priority=ActivityPriority.MEDIUM,
    estimated_duration_minutes=30,
):
    """
    Create a CropPlanActivityRequest.
    """

    return CropPlanActivityRequest(
        activity_type=activity_type,
        title=title,
        description=description,
        day=day,
        priority=priority,
        estimated_duration_minutes=(
            estimated_duration_minutes
        ),
    )


def make_stage_request(
    stage_order=1,
    name="Land Preparation",
    description="Stage description",
    start_day=1,
    end_day=10,
    activities=None,
):
    """
    Create a CropPlanStageRequest.
    """

    return CropPlanStageRequest(
        name=name,
        description=description,
        stage_order=stage_order,
        start_day=start_day,
        end_day=end_day,
        activities=activities or [],
    )


def make_request(
    stages=None,
    start_date=date(
        2026,
        8,
        10,
    ),
):
    """
    Create a CropPlanGenerateRequest.
    """

    return CropPlanGenerateRequest(
        start_date=start_date,
        stages=stages or [],
    )


# ============================================================
# MOCK ACTIVITY REPOSITORY
# ============================================================


def mock_activity_repository(
    crop,
):
    """
    Create ActivityRepository mock.
    """

    repository = MagicMock()

    repository.db = MagicMock()

    repository.db.query.return_value.filter.return_value.first.return_value = (
        crop
    )

    repository.db.refresh.side_effect = (
        lambda obj: None
    )

    repository.refresh.side_effect = (
        lambda obj: None
    )

    return repository


# ============================================================
# MOCK STAGE REPOSITORY
# ============================================================


def configure_stage_repository_ids(
    stage_repository,
):
    """
    Simulate SQLAlchemy UUID generation
    for CropStage objects.
    """

    def create_without_commit(
        stage,
    ):

        if stage.id is None:
            stage.id = uuid4()

        if not hasattr(
            stage,
            "activities",
        ):
            stage.activities = []

        return stage

    stage_repository.create_without_commit.side_effect = (
        create_without_commit
    )


# ============================================================
# MOCK ACTIVITY RELATIONSHIP
# ============================================================


def configure_activity_repository(
    activity_repository,
    stage_repository,
):
    """
    Simulate:

        CropStage.activities

    SQLAlchemy normally populates this relationship.

    The unit-test mock must do it manually.
    """

    def create_many(
        activities,
    ):

        for activity in activities:

            if activity.id is None:
                activity.id = uuid4()

            # ------------------------------------------------
            # Find the generated stage
            # ------------------------------------------------

            for call in (
                stage_repository
                .create_without_commit
                .call_args_list
            ):

                stage = call.args[0]

                if stage.id == activity.stage_id:

                    if not hasattr(
                        stage,
                        "activities",
                    ):
                        stage.activities = []

                    stage.activities.append(
                        activity,
                    )

                    break

        return activities

    activity_repository.create_many.side_effect = (
        create_many
    )


# ============================================================
# VALIDATE STAGE REQUESTS
# ============================================================


def test_validate_stage_requests_requires_at_least_one_stage():

    request = make_request(
        stages=[],
    )

    with pytest.raises(
        ValidationError,
        match="At least one crop stage is required",
    ):
        service._validate_stage_requests(
            request,
        )


def test_validate_stage_requests_accepts_valid_request():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                start_day=1,
                end_day=10,
            )
        ],
    )

    service._validate_stage_requests(
        request,
    )


def test_validate_stage_requests_rejects_invalid_stage_order():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=2,
                start_day=1,
                end_day=10,
            )
        ],
    )

    with pytest.raises(
        ValidationError,
        match="continuous stage orders",
    ):
        service._validate_stage_requests(
            request,
        )


def test_validate_stage_requests_rejects_missing_stage_order():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                start_day=1,
                end_day=10,
            ),
            make_stage_request(
                stage_order=3,
                start_day=11,
                end_day=20,
            ),
        ],
    )

    with pytest.raises(
        ValidationError,
        match="continuous stage orders",
    ):
        service._validate_stage_requests(
            request,
        )


def test_validate_stage_requests_rejects_invalid_stage_timeline():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                start_day=10,
                end_day=5,
            )
        ],
    )

    with pytest.raises(
        ValidationError,
        match="greater than or equal",
    ):
        service._validate_stage_requests(
            request,
        )


def test_validate_stage_requests_rejects_activity_before_stage():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                start_day=5,
                end_day=10,
                activities=[
                    make_activity_request(
                        day=3,
                        title="Irrigation",
                        activity_type=(
                            ActivityType.IRRIGATION
                        ),
                    )
                ],
            )
        ],
    )

    with pytest.raises(
        ValidationError,
        match="scheduled before its stage starts",
    ):
        service._validate_stage_requests(
            request,
        )


def test_validate_stage_requests_rejects_activity_after_stage():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                start_day=1,
                end_day=5,
                activities=[
                    make_activity_request(
                        day=8,
                        title="Irrigation",
                        activity_type=(
                            ActivityType.IRRIGATION
                        ),
                    )
                ],
            )
        ],
    )

    with pytest.raises(
        ValidationError,
        match="scheduled after its stage ends",
    ):
        service._validate_stage_requests(
            request,
        )


def test_validate_stage_requests_accepts_activity_on_stage_start():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                start_day=5,
                end_day=10,
                activities=[
                    make_activity_request(
                        day=5,
                    )
                ],
            )
        ],
    )

    service._validate_stage_requests(
        request,
    )


def test_validate_stage_requests_accepts_activity_on_stage_end():

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                start_day=1,
                end_day=10,
                activities=[
                    make_activity_request(
                        day=10,
                    )
                ],
            )
        ],
    )

    service._validate_stage_requests(
        request,
    )


# ============================================================
# START DATE VALIDATION
# ============================================================


def test_validate_start_date_accepts_crop_sowing_date():

    crop = make_crop()

    service._validate_start_date(
        crop,
        date(
            2026,
            8,
            10,
        ),
    )


def test_validate_start_date_rejects_different_date():

    crop = make_crop()

    with pytest.raises(
        ValidationError,
        match="must match the crop season sowing date",
    ):
        service._validate_start_date(
            crop,
            date(
                2026,
                8,
                11,
            ),
        )


# ============================================================
# CROP PLAN STATUS VALIDATION
# ============================================================


def test_validate_crop_plan_status_accepts_planned_crop():

    crop = make_crop()

    service._validate_crop_plan_status(
        crop,
    )


@pytest.mark.parametrize(
    "status",
    [
        CropSeasonStatus.ACTIVE,
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ],
)
def test_validate_crop_plan_status_rejects_non_planned(
    status,
):

    crop = make_crop()

    crop.status = status

    with pytest.raises(
        ValidationError,
        match="only be generated while the crop season is planned",
    ):
        service._validate_crop_plan_status(
            crop,
        )


# ============================================================
# ACTIVITY DATE CALCULATION
# ============================================================


@pytest.mark.parametrize(
    "relative_day,expected_date",
    [
        (
            1,
            date(
                2026,
                8,
                10,
            ),
        ),
        (
            2,
            date(
                2026,
                8,
                11,
            ),
        ),
        (
            3,
            date(
                2026,
                8,
                12,
            ),
        ),
        (
            10,
            date(
                2026,
                8,
                19,
            ),
        ),
    ],
)
def test_calculate_activity_date(
    relative_day,
    expected_date,
):

    result = service._calculate_activity_date(
        date(
            2026,
            8,
            10,
        ),
        relative_day,
    )

    assert result == expected_date


# ============================================================
# GET CROP SEASON
# ============================================================


def test_get_crop_season():

    crop = make_crop()

    repository = mock_activity_repository(
        crop,
    )

    result = service._get_crop_season(
        repository,
        crop.id,
    )

    assert result == crop


def test_get_crop_season_not_found():

    repository = MagicMock()

    repository.db = MagicMock()

    repository.db.query.return_value.filter.return_value.first.return_value = (
        None
    )

    with pytest.raises(
        ValidationError,
        match="Crop season not found",
    ):
        service._get_crop_season(
            repository,
            uuid4(),
        )


# ============================================================
# GENERATE CROP PLAN
# ============================================================


def test_generate_crop_plan_requires_stages():

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    request = make_request(
        stages=[],
    )

    with pytest.raises(
        ValidationError,
        match="At least one crop stage",
    ):
        service.generate_crop_plan(
            activity_repository=activity_repository,
            crop_season_id=crop.id,
            request=request,
        )


def test_generate_crop_plan_rejects_existing_plan(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    existing_stage = CropStage(
        id=uuid4(),
        crop_season_id=crop.id,
        name="Existing Stage",
        stage_order=1,
        start_day=1,
        end_day=10,
        status=CropStageStatus.PENDING,
    )

    stage_repository.get_all_by_crop_season.return_value = [
        existing_stage
    ]

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    request = make_request(
        stages=[
            make_stage_request()
        ],
    )

    with pytest.raises(
        ValidationError,
        match="A crop plan already exists",
    ):
        service.generate_crop_plan(
            activity_repository=activity_repository,
            crop_season_id=crop.id,
            request=request,
        )


def test_generate_crop_plan_creates_stages_and_activities(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    stage_repository.get_all_by_crop_season.return_value = []

    configure_stage_repository_ids(
        stage_repository,
    )

    configure_activity_repository(
        activity_repository,
        stage_repository,
    )

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                name="Land Preparation",
                start_day=1,
                end_day=10,
                activities=[
                    make_activity_request(
                        day=2,
                        title="Prepare field",
                        activity_type=(
                            ActivityType.LAND_PREPARATION
                        ),
                    ),
                ],
            ),
        ],
    )

    result = service.generate_crop_plan(
        activity_repository=activity_repository,
        crop_season_id=crop.id,
        request=request,
    )

    # ========================================================
    # PLAN
    # ========================================================

    assert result.crop_season_id == crop.id

    assert result.status == (
        CropSeasonStatus.PLANNED
    )

    assert result.start_date == date(
        2026,
        8,
        10,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    assert result.total_stages == 1

    assert result.total_activities == 1

    # ========================================================
    # STAGE
    # ========================================================

    assert len(result.stages) == 1

    stage = result.stages[0]

    assert stage.id is not None

    assert stage.crop_season_id == crop.id

    assert stage.name == (
        "Land Preparation"
    )

    assert stage.description == (
        "Stage description"
    )

    assert stage.stage_order == 1

    assert stage.start_day == 1

    assert stage.end_day == 10

    # ========================================================
    # ACTIVITY
    # ========================================================

    assert len(stage.activities) == 1

    activity = stage.activities[0]

    assert activity.id is not None

    assert activity.crop_season_id == crop.id

    assert activity.stage_id == stage.id

    assert activity.activity_type == (
        ActivityType.LAND_PREPARATION
    )

    assert activity.title == (
        "Prepare field"
    )

    assert activity.description == (
        "Activity description"
    )

    assert activity.scheduled_date == date(
        2026,
        8,
        11,
    )

    assert activity.original_scheduled_date == date(
        2026,
        8,
        11,
    )

    assert activity.priority == (
        ActivityPriority.MEDIUM
    )

    assert (
        activity.estimated_duration_minutes
        == 30
    )

    # ========================================================
    # REPOSITORY
    # ========================================================

    activity_repository.create_many.assert_called_once()

    activity_repository.commit.assert_called_once()


def test_generate_crop_plan_without_activities(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    stage_repository.get_all_by_crop_season.return_value = []

    configure_stage_repository_ids(
        stage_repository,
    )

    configure_activity_repository(
        activity_repository,
        stage_repository,
    )

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    request = make_request(
        stages=[
            make_stage_request(
                activities=[],
            )
        ],
    )

    result = service.generate_crop_plan(
        activity_repository=activity_repository,
        crop_season_id=crop.id,
        request=request,
    )

    assert result.total_stages == 1

    assert result.total_activities == 0

    assert len(result.stages) == 1

    assert result.stages[0].activities == []


# ============================================================
# MULTIPLE STAGES
# ============================================================


def test_generate_crop_plan_creates_multiple_stages(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    stage_repository.get_all_by_crop_season.return_value = []

    configure_stage_repository_ids(
        stage_repository,
    )

    configure_activity_repository(
        activity_repository,
        stage_repository,
    )

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                name="Land Preparation",
                start_day=1,
                end_day=10,
            ),
            make_stage_request(
                stage_order=2,
                name="Sowing",
                start_day=11,
                end_day=20,
            ),
            make_stage_request(
                stage_order=3,
                name="Growth",
                start_day=21,
                end_day=50,
            ),
        ],
    )

    result = service.generate_crop_plan(
        activity_repository=activity_repository,
        crop_season_id=crop.id,
        request=request,
    )

    assert result.total_stages == 3

    assert result.total_activities == 0

    assert [
        stage.stage_order
        for stage in result.stages
    ] == [
        1,
        2,
        3,
    ]

    assert [
        stage.name
        for stage in result.stages
    ] == [
        "Land Preparation",
        "Sowing",
        "Growth",
    ]


# ============================================================
# GENERATE ROLLBACK
# ============================================================


def test_generate_crop_plan_rolls_back_on_error(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    stage_repository.get_all_by_crop_season.return_value = []

    configure_stage_repository_ids(
        stage_repository,
    )

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    activity_repository.create_many.side_effect = (
        RuntimeError(
            "Database failure"
        )
    )

    request = make_request(
        stages=[
            make_stage_request(
                activities=[
                    make_activity_request(),
                ],
            )
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Database failure",
    ):
        service.generate_crop_plan(
            activity_repository=activity_repository,
            crop_season_id=crop.id,
            request=request,
        )

    activity_repository.rollback.assert_called_once()


# ============================================================
# REGENERATE CROP PLAN
# ============================================================


def test_regenerate_crop_plan_deletes_old_data_first(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    configure_stage_repository_ids(
        stage_repository,
    )

    configure_activity_repository(
        activity_repository,
        stage_repository,
    )

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    request = make_request(
        stages=[
            make_stage_request(
                stage_order=1,
                name="New Stage",
                start_day=1,
                end_day=10,
                activities=[
                    make_activity_request(
                        day=2,
                        title="New Activity",
                        activity_type=(
                            ActivityType.IRRIGATION
                        ),
                    ),
                ],
            )
        ],
    )

    result = service.regenerate_crop_plan(
        activity_repository=activity_repository,
        crop_season_id=crop.id,
        request=request,
    )

    # ========================================================
    # DELETE OLD ACTIVITIES
    # ========================================================

    activity_repository.delete_all_by_crop_season.assert_called_once_with(
        crop.id,
    )

    # ========================================================
    # DELETE OLD STAGES
    # ========================================================

    stage_repository.delete_all_by_crop_season.assert_called_once_with(
        crop.id,
    )

    # ========================================================
    # RESULT
    # ========================================================

    assert result.crop_season_id == crop.id

    assert result.total_stages == 1

    assert result.total_activities == 1

    assert len(result.stages) == 1

    stage = result.stages[0]

    assert stage.id is not None

    assert stage.name == "New Stage"

    assert len(stage.activities) == 1

    activity = stage.activities[0]

    assert activity.id is not None

    assert activity.title == (
        "New Activity"
    )

    assert activity.activity_type == (
        ActivityType.IRRIGATION
    )

    assert activity.scheduled_date == date(
        2026,
        8,
        11,
    )

    # ========================================================
    # COMMIT
    # ========================================================

    activity_repository.commit.assert_called_once()


def test_regenerate_crop_plan_rolls_back_on_error(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    configure_stage_repository_ids(
        stage_repository,
    )

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    activity_repository.create_many.side_effect = (
        RuntimeError(
            "Regeneration failed"
        )
    )

    request = make_request(
        stages=[
            make_stage_request(
                activities=[
                    make_activity_request(),
                ],
            )
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Regeneration failed",
    ):
        service.regenerate_crop_plan(
            activity_repository=activity_repository,
            crop_season_id=crop.id,
            request=request,
        )

    activity_repository.rollback.assert_called_once()


# ============================================================
# GET CROP PLAN
# ============================================================


def test_get_crop_plan_returns_generated_plan(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    stage = CropStage(
        id=uuid4(),
        crop_season_id=crop.id,
        name="Land Preparation",
        description="Stage description",
        stage_order=1,
        start_day=1,
        end_day=10,
        status=CropStageStatus.PENDING,
    )

    activity = Activity(
        id=uuid4(),
        crop_season_id=crop.id,
        stage_id=stage.id,
        activity_type=(
            ActivityType.LAND_PREPARATION
        ),
        title="Prepare field",
        description="Activity description",
        scheduled_date=date(
            2026,
            8,
            11,
        ),
        original_scheduled_date=date(
            2026,
            8,
            11,
        ),
        completed_date=None,
        status=ActivityStatus.PENDING,
        notes=None,
        priority=ActivityPriority.MEDIUM,
        estimated_duration_minutes=30,
        source=ActivitySource.AI_PLANNED,
    )

    stage.activities = [
        activity
    ]

    stage_repository.get_all_by_crop_season.return_value = [
        stage
    ]

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    result = service.get_crop_plan(
        activity_repository=activity_repository,
        crop_season_id=crop.id,
    )

    assert result.crop_season_id == crop.id

    assert result.status == (
        CropSeasonStatus.PLANNED
    )

    assert result.start_date == date(
        2026,
        8,
        10,
    )

    assert result.total_stages == 1

    assert result.total_activities == 1

    assert len(result.stages) == 1

    assert len(
        result.stages[0].activities
    ) == 1


def test_get_crop_plan_not_found():

    repository = MagicMock()

    repository.db = MagicMock()

    repository.db.query.return_value.filter.return_value.first.return_value = (
        None
    )

    with pytest.raises(
        ValidationError,
        match="Crop season not found",
    ):
        service.get_crop_plan(
            activity_repository=repository,
            crop_season_id=uuid4(),
        )


def test_get_crop_plan_when_no_stages(
    monkeypatch,
):

    crop = make_crop()

    activity_repository = (
        mock_activity_repository(
            crop,
        )
    )

    stage_repository = MagicMock()

    stage_repository.get_all_by_crop_season.return_value = []

    monkeypatch.setattr(
        service,
        "CropStageRepository",
        lambda db: stage_repository,
    )

    with pytest.raises(
        ValidationError,
        match="No crop plan has been generated yet",
    ):
        service.get_crop_plan(
            activity_repository=activity_repository,
            crop_season_id=crop.id,
        )


# ============================================================
# RESPONSE BUILDER
# ============================================================


def test_build_crop_plan_response_without_activities():

    crop = make_crop()

    stage = CropStage(
        id=uuid4(),
        crop_season_id=crop.id,
        name="Land Preparation",
        description=None,
        stage_order=1,
        start_day=1,
        end_day=10,
        status=CropStageStatus.PENDING,
    )

    stage.activities = []

    result = service._build_crop_plan_response(
        crop_season=crop,
        stages=[
            stage,
        ],
    )

    assert result.total_stages == 1

    assert result.total_activities == 0

    assert result.stages[0].activities == []


def test_build_crop_plan_response_counts_activities():

    crop = make_crop()

    stage = CropStage(
        id=uuid4(),
        crop_season_id=crop.id,
        name="Land Preparation",
        description=None,
        stage_order=1,
        start_day=1,
        end_day=10,
        status=CropStageStatus.PENDING,
    )

    activity = Activity(
        id=uuid4(),
        crop_season_id=crop.id,
        stage_id=stage.id,
        activity_type=(
            ActivityType.LAND_PREPARATION
        ),
        title="Prepare field",
        description=None,
        scheduled_date=date(
            2026,
            8,
            11,
        ),
        original_scheduled_date=date(
            2026,
            8,
            11,
        ),
        completed_date=None,
        status=ActivityStatus.PENDING,
        notes=None,
        priority=ActivityPriority.MEDIUM,
        estimated_duration_minutes=30,
        source=ActivitySource.AI_PLANNED,
    )

    stage.activities = [
        activity
    ]

    result = service._build_crop_plan_response(
        crop_season=crop,
        stages=[
            stage,
        ],
    )

    assert result.total_stages == 1

    assert result.total_activities == 1

    assert len(
        result.stages[0].activities
    ) == 1