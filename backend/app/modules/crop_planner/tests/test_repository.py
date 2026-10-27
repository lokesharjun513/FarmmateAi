from uuid import uuid4

from app.modules.activity.models import Activity
from app.modules.crop_planner.repository import CropPlannerRepository
from app.modules.crop_stage.models import CropStage


# ============================================================
# HELPERS
# ============================================================


def create_stage(
    *,
    crop_season_id,
    stage_order=1,
):
    return CropStage(
        id=uuid4(),
        crop_season_id=crop_season_id,
        name=f"Stage {stage_order}",
        description=f"Description for stage {stage_order}.",
        stage_order=stage_order,
        start_day=1,
        end_day=30,
    )


def create_activity(
    *,
    crop_season_id,
    stage_id,
):
    from datetime import date

    from app.modules.activity.models import (
        ActivityPriority,
        ActivitySource,
        ActivityStatus,
        ActivityType,
    )

    return Activity(
        id=uuid4(),
        crop_season_id=crop_season_id,
        stage_id=stage_id,
        activity_type=ActivityType.IRRIGATION,
        title="Irrigate field",
        description="Provide irrigation to the crop.",
        scheduled_date=date.today(),
        original_scheduled_date=None,
        completed_date=None,
        status=ActivityStatus.PENDING,
        notes=None,
        priority=ActivityPriority.MEDIUM,
        estimated_duration_minutes=30,
        source=ActivitySource.AI_PLANNED,
    )


# ============================================================
# HAS PLAN
# ============================================================


def test_has_plan_returns_false_when_no_stage_exists(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    assert repository.has_plan(
        crop_season_id,
    ) is False


def test_has_plan_returns_true_when_stage_exists(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    db.add(stage)
    db.commit()

    assert repository.has_plan(
        crop_season_id,
    ) is True


def test_has_plan_is_isolated_by_crop_season(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()
    other_crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    db.add(stage)
    db.commit()

    assert repository.has_plan(
        crop_season_id,
    ) is True

    assert repository.has_plan(
        other_crop_season_id,
    ) is False


# ============================================================
# CREATE STAGE
# ============================================================


def test_create_stage_persists_stage(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    result = repository.create_stage(
        stage,
    )

    assert result is stage
    assert result.id == stage.id

    db.commit()

    saved = (
        db.query(CropStage)
        .filter(
            CropStage.id == stage.id,
        )
        .first()
    )

    assert saved is not None
    assert saved.crop_season_id == crop_season_id
    assert saved.name == "Stage 1"


def test_create_stage_flushes_id_and_data(db):

    repository = CropPlannerRepository(db)

    stage = CropStage(
        crop_season_id=uuid4(),
        name="Vegetative",
        description="Vegetative growth stage.",
        stage_order=1,
        start_day=1,
        end_day=30,
    )

    result = repository.create_stage(
        stage,
    )

    assert result.id is not None

    assert result.name == "Vegetative"

    assert result.stage_order == 1


# ============================================================
# CREATE ACTIVITIES
# ============================================================


def test_create_activities_returns_empty_list_for_empty_input(
    db,
):

    repository = CropPlannerRepository(db)

    result = repository.create_activities(
        [],
    )

    assert result == []


def test_create_activities_persists_multiple_activities(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    activities = [
        create_activity(
            crop_season_id=crop_season_id,
            stage_id=stage.id,
        ),
        create_activity(
            crop_season_id=crop_season_id,
            stage_id=stage.id,
        ),
    ]

    result = repository.create_activities(
        activities,
    )

    assert result == activities
    assert len(result) == 2

    db.commit()

    saved = (
        db.query(Activity)
        .filter(
            Activity.crop_season_id
            == crop_season_id,
        )
        .all()
    )

    assert len(saved) == 2


def test_create_activities_flushes_records(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    activity = create_activity(
        crop_season_id=crop_season_id,
        stage_id=stage.id,
    )

    result = repository.create_activities(
        [activity],
    )

    assert result[0] is activity
    assert result[0].id is not None


def test_create_activities_preserves_order(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    first = create_activity(
        crop_season_id=crop_season_id,
        stage_id=stage.id,
    )

    second = create_activity(
        crop_season_id=crop_season_id,
        stage_id=stage.id,
    )

    result = repository.create_activities(
        [first, second],
    )

    assert result[0] is first
    assert result[1] is second


# ============================================================
# COMMIT
# ============================================================


def test_commit_persists_changes(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    repository.commit()

    saved = (
        db.query(CropStage)
        .filter(
            CropStage.id == stage.id,
        )
        .first()
    )

    assert saved is not None


# ============================================================
# ROLLBACK
# ============================================================


def test_rollback_discards_uncommitted_changes(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    repository.rollback()

    saved = (
        db.query(CropStage)
        .filter(
            CropStage.id == stage.id,
        )
        .first()
    )

    assert saved is None


# ============================================================
# REFRESH
# ============================================================


def test_refresh_returns_same_instance(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    repository.commit()

    result = repository.refresh(
        stage,
    )

    assert result is stage


def test_refresh_loads_persisted_values(db):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    repository.commit()

    stage.name = "Temporary Name"

    repository.refresh(
        stage,
    )

    assert stage.name == "Stage 1"


# ============================================================
# TRANSACTION FLOW
# ============================================================


def test_stage_and_activities_can_be_saved_in_same_transaction(
    db,
):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    activities = [
        create_activity(
            crop_season_id=crop_season_id,
            stage_id=stage.id,
        ),
        create_activity(
            crop_season_id=crop_season_id,
            stage_id=stage.id,
        ),
    ]

    repository.create_activities(
        activities,
    )

    repository.commit()

    saved_stage = (
        db.query(CropStage)
        .filter(
            CropStage.id == stage.id,
        )
        .first()
    )

    saved_activities = (
        db.query(Activity)
        .filter(
            Activity.stage_id == stage.id,
        )
        .all()
    )

    assert saved_stage is not None
    assert len(saved_activities) == 2


def test_rollback_removes_stage_and_activities_together(
    db,
):

    repository = CropPlannerRepository(db)

    crop_season_id = uuid4()

    stage = create_stage(
        crop_season_id=crop_season_id,
    )

    repository.create_stage(
        stage,
    )

    activity = create_activity(
        crop_season_id=crop_season_id,
        stage_id=stage.id,
    )

    repository.create_activities(
        [activity],
    )

    repository.rollback()

    saved_stage = (
        db.query(CropStage)
        .filter(
            CropStage.id == stage.id,
        )
        .first()
    )

    saved_activity = (
        db.query(Activity)
        .filter(
            Activity.id == activity.id,
        )
        .first()
    )

    assert saved_stage is None
    assert saved_activity is None