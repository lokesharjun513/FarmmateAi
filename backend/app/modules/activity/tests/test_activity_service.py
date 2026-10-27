from datetime import date
from uuid import uuid4

import pytest

from app.modules.activity.models import (
    Activity,
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
    ActivityType,
)

from app.modules.activity.repository import (
    ActivityRepository,
)

from app.modules.activity.schemas import (
    ActivityUpdateRequest,
)

from app.modules.activity.service import (
    complete_activity,
    delete_activity,
    skip_activity,
    start_activity,
    update_activity,
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
# HELPERS
# ============================================================


def create_test_crop_season(
    db,
    *,
    status=CropSeasonStatus.ACTIVE,
):
    """
    Create a real CropSeason for activity service tests.

    Activity lifecycle operations require a real crop season.

    Lifecycle:

        PLANNED
        ACTIVE
        HARVESTED
        CANCELLED
    """

    crop_season = CropSeason(
        farm_id=uuid4(),

        crop_name="Rice",

        crop_variety="BPT",

        land_area=1.0,

        land_unit="Acres",

        season=FarmingSeason.KHARIF,

        year=2026,

        sowing_date=date.today(),

        expected_harvest_date=None,

        harvested_date=None,

        status=status,

        is_active=(
            status == CropSeasonStatus.ACTIVE
        ),

        notes=None,
    )

    db.add(crop_season)

    db.commit()

    db.refresh(crop_season)

    return crop_season


def create_activity_object(
    db,
    *,
    status=ActivityStatus.PENDING,
    crop_season_status=CropSeasonStatus.ACTIVE,
):
    """
    Create a valid Activity together with a real CropSeason.

    Activity lifecycle rules:

        PENDING
            completed_date = None

        IN_PROGRESS
            completed_date = None

        COMPLETED
            completed_date = today

        SKIPPED
            completed_date = today
    """

    crop_season = create_test_crop_season(
        db,
        status=crop_season_status,
    )

    completed_date = None

    if status in (
        ActivityStatus.COMPLETED,
        ActivityStatus.SKIPPED,
    ):
        completed_date = date.today()

    activity = Activity(
        crop_season_id=crop_season.id,

        # Keep the ORM relationship explicitly populated.
        crop_season=crop_season,

        stage_id=None,

        activity_type=ActivityType.IRRIGATION,

        title="Irrigate field",

        description="Water the crop.",

        scheduled_date=date.today(),

        original_scheduled_date=date.today(),

        completed_date=completed_date,

        status=status,

        priority=ActivityPriority.MEDIUM,

        source=ActivitySource.FARMER_ADDED,

        notes=None,

        estimated_duration_minutes=60,
    )

    db.add(activity)

    db.commit()

    db.refresh(activity)

    return activity


# ============================================================
# START ACTIVITY
# ============================================================


def test_start_activity(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    repository = ActivityRepository(db)

    result = start_activity(
        repository,
        activity,
    )

    assert result.status == ActivityStatus.IN_PROGRESS


# ============================================================
# START ALREADY IN-PROGRESS
# ============================================================


def test_start_activity_is_idempotent(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.IN_PROGRESS,
    )

    repository = ActivityRepository(db)

    result = start_activity(
        repository,
        activity,
    )

    assert result.status == ActivityStatus.IN_PROGRESS


# ============================================================
# START COMPLETED
# ============================================================


def test_completed_activity_cannot_start(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.COMPLETED,
    )

    repository = ActivityRepository(db)

    with pytest.raises(
        ValidationError,
        match="Completed activity cannot be started again",
    ):
        start_activity(
            repository,
            activity,
        )


# ============================================================
# START SKIPPED
# ============================================================


def test_skipped_activity_cannot_start(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.SKIPPED,
    )

    repository = ActivityRepository(db)

    with pytest.raises(
        ValidationError,
        match="Skipped activity cannot be started again",
    ):
        start_activity(
            repository,
            activity,
        )


# ============================================================
# COMPLETE
# ============================================================


def test_complete_activity(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.IN_PROGRESS,
    )

    repository = ActivityRepository(db)

    result = complete_activity(
        repository,
        activity,
    )

    assert result.status == ActivityStatus.COMPLETED

    assert result.completed_date == date.today()


# ============================================================
# COMPLETE ALREADY COMPLETED
# ============================================================


def test_complete_activity_is_idempotent(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.COMPLETED,
    )

    repository = ActivityRepository(db)

    result = complete_activity(
        repository,
        activity,
    )

    assert result.status == ActivityStatus.COMPLETED

    assert result.completed_date == date.today()


# ============================================================
# COMPLETE PENDING
# ============================================================


def test_pending_activity_cannot_complete(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    repository = ActivityRepository(db)

    with pytest.raises(
        ValidationError,
        match="Only an activity in progress can be completed",
    ):
        complete_activity(
            repository,
            activity,
        )


# ============================================================
# COMPLETE SKIPPED
# ============================================================


def test_skipped_activity_cannot_complete(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.SKIPPED,
    )

    repository = ActivityRepository(db)

    with pytest.raises(
        ValidationError,
        match="Skipped activity cannot be completed",
    ):
        complete_activity(
            repository,
            activity,
        )


# ============================================================
# SKIP PENDING
# ============================================================


def test_skip_pending_activity(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    repository = ActivityRepository(db)

    result = skip_activity(
        repository,
        activity,
    )

    assert result.status == ActivityStatus.SKIPPED

    assert result.completed_date == date.today()


# ============================================================
# SKIP IN-PROGRESS
# ============================================================


def test_skip_in_progress_activity(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.IN_PROGRESS,
    )

    repository = ActivityRepository(db)

    result = skip_activity(
        repository,
        activity,
    )

    assert result.status == ActivityStatus.SKIPPED

    assert result.completed_date == date.today()


# ============================================================
# SKIP ALREADY SKIPPED
# ============================================================


def test_skip_activity_is_idempotent(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.SKIPPED,
    )

    repository = ActivityRepository(db)

    result = skip_activity(
        repository,
        activity,
    )

    assert result.status == ActivityStatus.SKIPPED

    assert result.completed_date == date.today()


# ============================================================
# COMPLETED CANNOT SKIP
# ============================================================


def test_completed_activity_cannot_skip(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.COMPLETED,
    )

    repository = ActivityRepository(db)

    with pytest.raises(
        ValidationError,
        match="Completed activity cannot be skipped",
    ):
        skip_activity(
            repository,
            activity,
        )


# ============================================================
# UPDATE PENDING
# ============================================================


def test_update_pending_activity(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    repository = ActivityRepository(db)

    request = ActivityUpdateRequest(
        title="Updated irrigation",
        priority=ActivityPriority.HIGH,
    )

    result = update_activity(
        repository,
        activity,
        request,
    )

    assert result.title == "Updated irrigation"

    assert result.priority == ActivityPriority.HIGH


# ============================================================
# UPDATE IN-PROGRESS
# ============================================================


def test_in_progress_activity_cannot_be_updated(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.IN_PROGRESS,
    )

    repository = ActivityRepository(db)

    request = ActivityUpdateRequest(
        title="Updated title",
    )

    with pytest.raises(
        ValidationError,
        match="In-progress activity cannot be edited",
    ):
        update_activity(
            repository,
            activity,
            request,
        )


# ============================================================
# UPDATE COMPLETED
# ============================================================


def test_completed_activity_cannot_be_updated(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.COMPLETED,
    )

    repository = ActivityRepository(db)

    request = ActivityUpdateRequest(
        title="Updated title",
    )

    with pytest.raises(
        ValidationError,
        match="Completed activity cannot be edited",
    ):
        update_activity(
            repository,
            activity,
            request,
        )


# ============================================================
# UPDATE SKIPPED
# ============================================================


def test_skipped_activity_cannot_be_updated(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.SKIPPED,
    )

    repository = ActivityRepository(db)

    request = ActivityUpdateRequest(
        title="Updated title",
    )

    with pytest.raises(
        ValidationError,
        match="Skipped activity cannot be edited",
    ):
        update_activity(
            repository,
            activity,
            request,
        )


# ============================================================
# RESCHEDULE
# ============================================================


def test_reschedule_preserves_original_date(db):

    original_date = date(
        2026,
        8,
        20,
    )

    new_date = date(
        2026,
        8,
        25,
    )

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    activity.scheduled_date = original_date

    activity.original_scheduled_date = original_date

    db.commit()

    db.refresh(activity)

    repository = ActivityRepository(db)

    request = ActivityUpdateRequest(
        scheduled_date=new_date,
    )

    result = update_activity(
        repository,
        activity,
        request,
    )

    assert result.scheduled_date == new_date

    assert (
        result.original_scheduled_date
        == original_date
    )


# ============================================================
# RESCHEDULE EARLIER
# ============================================================


def test_reschedule_to_earlier_date(db):

    original_date = date(
        2026,
        8,
        20,
    )

    earlier_date = date(
        2026,
        8,
        18,
    )

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    activity.scheduled_date = original_date

    activity.original_scheduled_date = original_date

    db.commit()

    db.refresh(activity)

    repository = ActivityRepository(db)

    request = ActivityUpdateRequest(
        scheduled_date=earlier_date,
    )

    result = update_activity(
        repository,
        activity,
        request,
    )

    assert result.scheduled_date == earlier_date

    assert (
        result.original_scheduled_date
        == original_date
    )


# ============================================================
# EMPTY UPDATE
# ============================================================


def test_empty_update_does_nothing(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    original_title = activity.title

    repository = ActivityRepository(db)

    request = ActivityUpdateRequest()

    result = update_activity(
        repository,
        activity,
        request,
    )

    assert result.title == original_title


# ============================================================
# DELETE PENDING
# ============================================================


def test_delete_pending_activity(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.PENDING,
    )

    repository = ActivityRepository(db)

    delete_activity(
        repository,
        activity,
    )

    result = repository.get_by_id(
        activity.id,
    )

    assert result is None


# ============================================================
# DELETE IN-PROGRESS
# ============================================================


def test_delete_in_progress_activity(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.IN_PROGRESS,
    )

    repository = ActivityRepository(db)

    delete_activity(
        repository,
        activity,
    )

    result = repository.get_by_id(
        activity.id,
    )

    assert result is None


# ============================================================
# COMPLETED CANNOT DELETE
# ============================================================


def test_completed_activity_cannot_delete(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.COMPLETED,
    )

    repository = ActivityRepository(db)

    with pytest.raises(
        ValidationError,
        match="Completed activity cannot be deleted",
    ):
        delete_activity(
            repository,
            activity,
        )


# ============================================================
# SKIPPED CANNOT DELETE
# ============================================================


def test_skipped_activity_cannot_delete(db):

    activity = create_activity_object(
        db,
        status=ActivityStatus.SKIPPED,
    )

    repository = ActivityRepository(db)

    with pytest.raises(
        ValidationError,
        match="Skipped activity cannot be deleted",
    ):
        delete_activity(
            repository,
            activity,
        )