from datetime import date
from uuid import UUID

from app.modules.activity.models import (
    Activity,
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
)

from app.modules.activity.repository import (
    ActivityRepository,
)

from app.modules.activity.schemas import (
    ActivityCreateRequest,
    ActivityInternalCreateRequest,
    ActivityUpdateRequest,
)

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.crop_stage.models import (
    CropStage,
)

from app.shared.exceptions import (
    ActivityNotFoundError,
    ValidationError,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _get_crop_season(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> CropSeason:
    """
    Get crop season by ID.

    Raises:
        ValidationError:
            If crop season does not exist.
    """

    crop_season = (
        repository.db.query(CropSeason)
        .filter(
            CropSeason.id == crop_season_id,
        )
        .first()
    )

    if crop_season is None:

        raise ValidationError(
            "Crop season not found."
        )

    return crop_season


def _get_stage(
    repository: ActivityRepository,
    stage_id: UUID,
) -> CropStage:
    """
    Get crop stage by ID.

    Raises:
        ValidationError:
            If crop stage does not exist.
    """

    stage = (
        repository.db.query(CropStage)
        .filter(
            CropStage.id == stage_id,
        )
        .first()
    )

    if stage is None:

        raise ValidationError(
            "Crop stage not found."
        )

    return stage


def _validate_stage_belongs_to_crop(
    repository: ActivityRepository,
    stage_id: UUID | None,
    crop_season_id: UUID,
) -> None:
    """
    Validate that an optional stage belongs to
    the same crop season as the activity.

    stage_id=None is valid because an activity
    may exist without a stage.
    """

    if stage_id is None:
        return

    stage = _get_stage(
        repository,
        stage_id,
    )

    if stage.crop_season_id != crop_season_id:

        raise ValidationError(
            "Activity stage does not belong to "
            "the specified crop season."
        )


def _validate_activity_creation_crop(
    crop_season: CropSeason,
) -> None:
    """
    Activities can be created while crop season is:

        PLANNED
        ACTIVE

    Activities cannot be created after:

        HARVESTED
        CANCELLED
    """

    if crop_season.status not in (
        CropSeasonStatus.PLANNED,
        CropSeasonStatus.ACTIVE,
    ):

        raise ValidationError(
            "Activities cannot be created for "
            "this crop season."
        )


def _validate_activity_update_status(
    activity: Activity,
) -> None:
    """
    Only PENDING activities can be edited.
    """

    if activity.status == ActivityStatus.IN_PROGRESS:

        raise ValidationError(
            "In-progress activity cannot be edited."
        )

    if activity.status == ActivityStatus.COMPLETED:

        raise ValidationError(
            "Completed activity cannot be edited."
        )

    if activity.status == ActivityStatus.SKIPPED:

        raise ValidationError(
            "Skipped activity cannot be edited."
        )

    if activity.status != ActivityStatus.PENDING:

        raise ValidationError(
            "Only pending activities can be edited."
        )


def _validate_activity_crop_for_update(
    activity: Activity,
) -> None:
    """
    Prevent activity modification after the crop
    season reaches a final state.
    """

    crop_season = activity.crop_season

    if crop_season is None:

        raise ValidationError(
            "Crop season not found."
        )

    if crop_season.status in (
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ):

        raise ValidationError(
            "Activities cannot be modified after "
            "the crop season has ended."
        )


def _validate_activity_crop_is_active(
    activity: Activity,
) -> CropSeason:
    """
    Activity lifecycle operations require
    an ACTIVE crop season.
    """

    crop_season = activity.crop_season

    if crop_season is None:

        raise ValidationError(
            "Crop season not found."
        )

    if crop_season.status != CropSeasonStatus.ACTIVE:

        raise ValidationError(
            "Activity can only be modified while "
            "the crop season is active."
        )

    return crop_season


# ============================================================
# STAGE / ACTIVITY COMPLETION
# ============================================================


def can_complete_stage_from_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> bool:
    """
    Determine whether all activities attached to a stage
    are finished.

    Rules:

        No activities
            -> False

        PENDING
            -> False

        IN_PROGRESS
            -> False

        COMPLETED
            -> Finished

        SKIPPED
            -> Finished

    This function DOES NOT complete the stage.

    Stage completion belongs to CropStageService.
    """

    if not repository.has_activities_by_stage(
        stage_id,
    ):

        return False

    return repository.all_finished_by_stage(
        stage_id,
    )


def get_stage_activity_completion(
    repository: ActivityRepository,
    stage_id: UUID,
) -> dict:
    """
    Return activity completion information
    for a crop stage.

    Example:

        {
            "total": 5,
            "completed": 3,
            "skipped": 1,
            "pending": 1,
            "in_progress": 0,
            "finished": 4,
            "is_finished": False,
            "completion_percentage": 80.0,
        }
    """

    total = repository.count_by_stage(
        stage_id,
    )

    completed = repository.count_completed_by_stage(
        stage_id,
    )

    skipped = repository.count_skipped_by_stage(
        stage_id,
    )

    pending = repository.count_pending_by_stage(
        stage_id,
    )

    in_progress = repository.count_in_progress_by_stage(
        stage_id,
    )

    finished = (
        completed
        + skipped
    )

    is_finished = (
        total > 0
        and pending == 0
        and in_progress == 0
    )

    completion_percentage = (
        (finished / total) * 100
        if total > 0
        else 0.0
    )

    return {
        "total": total,
        "completed": completed,
        "skipped": skipped,
        "pending": pending,
        "in_progress": in_progress,
        "finished": finished,
        "is_finished": is_finished,
        "completion_percentage": completion_percentage,
    }


def get_stage_activity_counts(
    repository: ActivityRepository,
    stage_id: UUID,
) -> dict:
    """
    Lightweight stage activity counters.

    Useful for dashboards and APIs.
    """

    return {
        "total": repository.count_by_stage(
            stage_id,
        ),
        "pending": repository.count_pending_by_stage(
            stage_id,
        ),
        "in_progress": repository.count_in_progress_by_stage(
            stage_id,
        ),
        "completed": repository.count_completed_by_stage(
            stage_id,
        ),
        "skipped": repository.count_skipped_by_stage(
            stage_id,
        ),
        "finished": repository.count_finished_by_stage(
            stage_id,
        ),
        "unfinished": repository.count_unfinished_by_stage(
            stage_id,
        ),
    }


# ============================================================
# CREATE FARMER ACTIVITY
# ============================================================


def create_activity(
    repository: ActivityRepository,
    crop_season_id: UUID,
    request: ActivityCreateRequest,
) -> Activity:

    crop_season = _get_crop_season(
        repository,
        crop_season_id,
    )

    _validate_activity_creation_crop(
        crop_season,
    )

    _validate_stage_belongs_to_crop(
        repository,
        request.stage_id,
        crop_season_id,
    )

    activity = Activity(
        crop_season_id=crop_season_id,
        stage_id=request.stage_id,
        activity_type=request.activity_type,
        title=request.title,
        description=request.description,
        scheduled_date=request.scheduled_date,
        original_scheduled_date=request.scheduled_date,
        completed_date=None,
        notes=request.notes,
        priority=request.priority,
        estimated_duration_minutes=(
            request.estimated_duration_minutes
        ),
        source=ActivitySource.FARMER_ADDED,
        status=ActivityStatus.PENDING,
    )

    try:

        return repository.create(
            activity,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# CREATE INTERNAL ACTIVITY
# ============================================================


def create_internal_activity(
    repository: ActivityRepository,
    crop_season_id: UUID,
    request: ActivityInternalCreateRequest,
) -> Activity:

    crop_season = _get_crop_season(
        repository,
        crop_season_id,
    )

    _validate_activity_creation_crop(
        crop_season,
    )

    _validate_stage_belongs_to_crop(
        repository,
        request.stage_id,
        crop_season_id,
    )

    activity = Activity(
        crop_season_id=crop_season_id,
        stage_id=request.stage_id,
        activity_type=request.activity_type,
        title=request.title,
        description=request.description,
        scheduled_date=request.scheduled_date,
        original_scheduled_date=request.scheduled_date,
        completed_date=None,
        notes=request.notes,
        priority=request.priority,
        estimated_duration_minutes=(
            request.estimated_duration_minutes
        ),
        source=request.source,
        status=ActivityStatus.PENDING,
    )

    try:

        return repository.create(
            activity,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# CREATE FARMER ACTIVITY WITHOUT COMMIT
# ============================================================


def create_activity_without_commit(
    repository: ActivityRepository,
    crop_season_id: UUID,
    request: ActivityCreateRequest,
) -> Activity:

    crop_season = _get_crop_season(
        repository,
        crop_season_id,
    )

    _validate_activity_creation_crop(
        crop_season,
    )

    _validate_stage_belongs_to_crop(
        repository,
        request.stage_id,
        crop_season_id,
    )

    activity = Activity(
        crop_season_id=crop_season_id,
        stage_id=request.stage_id,
        activity_type=request.activity_type,
        title=request.title,
        description=request.description,
        scheduled_date=request.scheduled_date,
        original_scheduled_date=request.scheduled_date,
        completed_date=None,
        notes=request.notes,
        priority=request.priority,
        estimated_duration_minutes=(
            request.estimated_duration_minutes
        ),
        source=ActivitySource.FARMER_ADDED,
        status=ActivityStatus.PENDING,
    )

    return repository.create_without_commit(
        activity,
    )


# ============================================================
# CREATE INTERNAL ACTIVITY WITHOUT COMMIT
# ============================================================


def create_internal_activity_without_commit(
    repository: ActivityRepository,
    crop_season_id: UUID,
    request: ActivityInternalCreateRequest,
) -> Activity:

    crop_season = _get_crop_season(
        repository,
        crop_season_id,
    )

    _validate_activity_creation_crop(
        crop_season,
    )

    _validate_stage_belongs_to_crop(
        repository,
        request.stage_id,
        crop_season_id,
    )

    activity = Activity(
        crop_season_id=crop_season_id,
        stage_id=request.stage_id,
        activity_type=request.activity_type,
        title=request.title,
        description=request.description,
        scheduled_date=request.scheduled_date,
        original_scheduled_date=request.scheduled_date,
        completed_date=None,
        notes=request.notes,
        priority=request.priority,
        estimated_duration_minutes=(
            request.estimated_duration_minutes
        ),
        source=request.source,
        status=ActivityStatus.PENDING,
    )

    return repository.create_without_commit(
        activity,
    )


# ============================================================
# GET ACTIVITY
# ============================================================


def get_activity(
    repository: ActivityRepository,
    activity_id: UUID,
) -> Activity:

    activity = repository.get_by_id(
        activity_id,
    )

    if activity is None:

        raise ActivityNotFoundError()

    return activity


# ============================================================
# GET ACTIVITY BY CROP SEASON
# ============================================================


def get_activity_by_crop_season(
    repository: ActivityRepository,
    crop_season_id: UUID,
    activity_id: UUID,
) -> Activity:

    activity = repository.get_by_crop_season_and_id(
        crop_season_id=crop_season_id,
        activity_id=activity_id,
    )

    if activity is None:

        raise ActivityNotFoundError()

    return activity


# ============================================================
# GET ALL CROP ACTIVITIES
# ============================================================


def get_crop_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_all_by_crop_season(
        crop_season_id,
    )


# ============================================================
# GET STAGE ACTIVITIES
# ============================================================


def get_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> list[Activity]:

    return repository.get_all_by_stage(
        stage_id,
    )


# ============================================================
# GET TODAY ACTIVITIES
# ============================================================


def get_today_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_today_activities(
        crop_season_id,
        date.today(),
    )


# ============================================================
# GET TODAY INCOMPLETE
# ============================================================


def get_today_incomplete_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_today_incomplete_activities(
        crop_season_id,
        date.today(),
    )


# ============================================================
# GET TODAY PENDING
# ============================================================


def get_today_pending_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_today_pending_activities(
        crop_season_id,
        date.today(),
    )


# ============================================================
# GET TODAY IN-PROGRESS
# ============================================================


def get_today_in_progress_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_today_in_progress_activities(
        crop_season_id,
        date.today(),
    )


# ============================================================
# GET TODAY COMPLETED
# ============================================================


def get_today_completed_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_today_completed_activities(
        crop_season_id,
        date.today(),
    )


# ============================================================
# GET UPCOMING
# ============================================================


def get_upcoming_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_upcoming_activities(
        crop_season_id,
        date.today(),
    )


# ============================================================
# GET OVERDUE
# ============================================================


def get_overdue_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_overdue_activities(
        crop_season_id,
        date.today(),
    )


# ============================================================
# GET PENDING
# ============================================================


def get_pending_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_pending_activities(
        crop_season_id,
    )


# ============================================================
# GET IN-PROGRESS
# ============================================================


def get_in_progress_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_in_progress_activities(
        crop_season_id,
    )


# ============================================================
# GET COMPLETED
# ============================================================


def get_completed_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_completed_activities(
        crop_season_id,
    )


# ============================================================
# GET SKIPPED
# ============================================================


def get_skipped_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> list[Activity]:

    return repository.get_skipped_activities(
        crop_season_id,
    )


# ============================================================
# GET BY STATUS
# ============================================================


def get_activities_by_status(
    repository: ActivityRepository,
    crop_season_id: UUID,
    activity_status: ActivityStatus,
) -> list[Activity]:

    return repository.get_by_status(
        crop_season_id,
        activity_status,
    )


# ============================================================
# GET BY DATE RANGE
# ============================================================


def get_activities_by_date_range(
    repository: ActivityRepository,
    crop_season_id: UUID,
    start_date: date,
    end_date: date,
) -> list[Activity]:

    if end_date < start_date:

        raise ValidationError(
            "End date must be greater than or equal "
            "to start date."
        )

    return repository.get_by_date_range(
        crop_season_id,
        start_date,
        end_date,
    )


# ============================================================
# GET BY SOURCE
# ============================================================


def get_activities_by_source(
    repository: ActivityRepository,
    crop_season_id: UUID,
    source: ActivitySource,
) -> list[Activity]:

    return repository.get_by_source(
        crop_season_id,
        source,
    )


# ============================================================
# GET BY PRIORITY
# ============================================================


def get_activities_by_priority(
    repository: ActivityRepository,
    crop_season_id: UUID,
    priority: ActivityPriority,
) -> list[Activity]:

    return repository.get_by_priority(
        crop_season_id,
        priority,
    )


# ============================================================
# GET LATEST ACTIVITY
# ============================================================


def get_latest_activity(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> Activity | None:

    return repository.get_latest_activity(
        crop_season_id,
    )


# ============================================================
# GET LATEST COMPLETED ACTIVITY
# ============================================================


def get_latest_completed_activity(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> Activity | None:

    return repository.get_latest_completed_activity(
        crop_season_id,
    )


# ============================================================
# UPDATE ACTIVITY
# ============================================================


def update_activity(
    repository: ActivityRepository,
    activity: Activity,
    request: ActivityUpdateRequest,
) -> Activity:

    _validate_activity_crop_for_update(
        activity,
    )

    _validate_activity_update_status(
        activity,
    )

    update_data = request.model_dump(
        exclude_unset=True,
    )

    if not update_data:

        return activity

    # --------------------------------------------------------
    # Validate stage.
    # --------------------------------------------------------

    if "stage_id" in update_data:

        _validate_stage_belongs_to_crop(
            repository=repository,
            stage_id=update_data["stage_id"],
            crop_season_id=activity.crop_season_id,
        )

    # --------------------------------------------------------
    # Preserve original scheduled date.
    # --------------------------------------------------------

    if "scheduled_date" in update_data:

        new_scheduled_date = update_data[
            "scheduled_date"
        ]

        if (
            new_scheduled_date is not None
            and new_scheduled_date != activity.scheduled_date
            and activity.original_scheduled_date is None
        ):

            activity.original_scheduled_date = (
                activity.scheduled_date
            )

    # --------------------------------------------------------
    # Apply changes.
    # --------------------------------------------------------

    for field, value in update_data.items():

        setattr(
            activity,
            field,
            value,
        )

    try:

        return repository.update(
            activity,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# START ACTIVITY
#
# PENDING
#    ↓
# IN_PROGRESS
# ============================================================


def start_activity(
    repository: ActivityRepository,
    activity: Activity,
) -> Activity:

    if activity.status == ActivityStatus.IN_PROGRESS:

        return activity

    if activity.status == ActivityStatus.COMPLETED:

        raise ValidationError(
            "Completed activity cannot be started again."
        )

    if activity.status == ActivityStatus.SKIPPED:

        raise ValidationError(
            "Skipped activity cannot be started again."
        )

    if activity.status != ActivityStatus.PENDING:

        raise ValidationError(
            "Only a pending activity can be started."
        )

    _validate_activity_crop_is_active(
        activity,
    )

    activity.status = ActivityStatus.IN_PROGRESS

    try:

        return repository.update(
            activity,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# COMPLETE ACTIVITY
#
# IN_PROGRESS
#       ↓
# COMPLETED
#
# completed_date = today
#
# IMPORTANT:
#
# This function completes only the activity.
#
# It does NOT directly complete the crop stage.
#
# After this operation, callers can check:
#
#     can_complete_stage_from_activities(...)
#
# ============================================================


def complete_activity(
    repository: ActivityRepository,
    activity: Activity,
) -> Activity:

    if activity.status == ActivityStatus.COMPLETED:

        return activity

    if activity.status == ActivityStatus.SKIPPED:

        raise ValidationError(
            "Skipped activity cannot be completed."
        )

    if activity.status != ActivityStatus.IN_PROGRESS:

        raise ValidationError(
            "Only an activity in progress "
            "can be completed."
        )

    _validate_activity_crop_is_active(
        activity,
    )

    activity.status = ActivityStatus.COMPLETED

    activity.completed_date = date.today()

    try:

        return repository.update(
            activity,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# SKIP ACTIVITY
#
# PENDING / IN_PROGRESS
#          ↓
#       SKIPPED
# ============================================================


def skip_activity(
    repository: ActivityRepository,
    activity: Activity,
) -> Activity:

    if activity.status == ActivityStatus.SKIPPED:

        return activity

    if activity.status == ActivityStatus.COMPLETED:

        raise ValidationError(
            "Completed activity cannot be skipped."
        )

    if activity.status not in (
        ActivityStatus.PENDING,
        ActivityStatus.IN_PROGRESS,
    ):

        raise ValidationError(
            "Only pending or in-progress activities "
            "can be skipped."
        )

    _validate_activity_crop_is_active(
        activity,
    )

    activity.status = ActivityStatus.SKIPPED

    activity.completed_date = date.today()

    try:

        return repository.update(
            activity,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# DELETE ACTIVITY
# ============================================================


def delete_activity(
    repository: ActivityRepository,
    activity: Activity,
) -> None:

    if activity.status == ActivityStatus.COMPLETED:

        raise ValidationError(
            "Completed activity cannot be deleted."
        )

    if activity.status == ActivityStatus.SKIPPED:

        raise ValidationError(
            "Skipped activity cannot be deleted."
        )

    crop_season = activity.crop_season

    if crop_season is None:

        raise ValidationError(
            "Crop season not found."
        )

    if crop_season.status in (
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ):

        raise ValidationError(
            "Activities cannot be deleted after "
            "the crop season has ended."
        )

    try:

        repository.delete(
            activity,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# DELETE ALL ACTIVITIES BY CROP SEASON
#
# Intended for PLANNED crop-plan regeneration.
# ============================================================


def delete_all_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> None:

    crop_season = _get_crop_season(
        repository,
        crop_season_id,
    )

    if crop_season.status != CropSeasonStatus.PLANNED:

        raise ValidationError(
            "Activities can only be regenerated "
            "while the crop season is planned."
        )

    repository.delete_all_by_crop_season(
        crop_season_id,
    )


# ============================================================
# COUNT ALL ACTIVITIES
# ============================================================


def count_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_by_crop_season(
        crop_season_id,
    )


# ============================================================
# COUNT PENDING
# ============================================================


def count_pending_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_by_status(
        crop_season_id,
        ActivityStatus.PENDING,
    )


# ============================================================
# COUNT IN-PROGRESS
# ============================================================


def count_in_progress_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_by_status(
        crop_season_id,
        ActivityStatus.IN_PROGRESS,
    )


# ============================================================
# COUNT COMPLETED
# ============================================================


def count_completed_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_by_status(
        crop_season_id,
        ActivityStatus.COMPLETED,
    )


# ============================================================
# COUNT SKIPPED
# ============================================================


def count_skipped_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_by_status(
        crop_season_id,
        ActivityStatus.SKIPPED,
    )


# ============================================================
# COUNT TODAY
# ============================================================


def count_today_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_today(
        crop_season_id,
        date.today(),
    )


# ============================================================
# COUNT TODAY PENDING
# ============================================================


def count_today_pending_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_pending_today(
        crop_season_id,
        date.today(),
    )


# ============================================================
# COUNT TODAY COMPLETED
# ============================================================


def count_today_completed_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_completed_today(
        crop_season_id,
        date.today(),
    )


# ============================================================
# COUNT TODAY SKIPPED
# ============================================================


def count_today_skipped_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_skipped_today(
        crop_season_id,
        date.today(),
    )


# ============================================================
# COUNT OVERDUE
# ============================================================


def count_overdue_activities(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> int:

    return repository.count_overdue(
        crop_season_id,
        date.today(),
    )


# ============================================================
# COUNT STAGE ACTIVITIES
# ============================================================


def count_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> int:

    return repository.count_by_stage(
        stage_id,
    )


# ============================================================
# COUNT UNFINISHED STAGE ACTIVITIES
# ============================================================


def count_unfinished_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> int:

    return repository.count_unfinished_by_stage(
        stage_id,
    )


# ============================================================
# COUNT FINISHED STAGE ACTIVITIES
# ============================================================


def count_finished_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> int:

    return repository.count_finished_by_stage(
        stage_id,
    )


# ============================================================
# COUNT COMPLETED STAGE ACTIVITIES
# ============================================================


def count_completed_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> int:

    return repository.count_completed_by_stage(
        stage_id,
    )


# ============================================================
# COUNT SKIPPED STAGE ACTIVITIES
# ============================================================


def count_skipped_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> int:

    return repository.count_skipped_by_stage(
        stage_id,
    )


# ============================================================
# COUNT PENDING STAGE ACTIVITIES
# ============================================================


def count_pending_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> int:

    return repository.count_pending_by_stage(
        stage_id,
    )


# ============================================================
# COUNT IN-PROGRESS STAGE ACTIVITIES
# ============================================================


def count_in_progress_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> int:

    return repository.count_in_progress_by_stage(
        stage_id,
    )


# ============================================================
# HAS IN-PROGRESS ACTIVITY
# ============================================================


def has_in_progress_activity(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> bool:

    return repository.has_in_progress_activity(
        crop_season_id,
    )


# ============================================================
# HAS PENDING ACTIVITY
# ============================================================


def has_pending_activity(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> bool:

    return repository.has_pending_activity(
        crop_season_id,
    )


# ============================================================
# HAS UNFINISHED ACTIVITY
# ============================================================


def has_unfinished_activity(
    repository: ActivityRepository,
    crop_season_id: UUID,
) -> bool:

    return repository.has_unfinished_activity(
        crop_season_id,
    )


# ============================================================
# HAS ACTIVITIES BY STAGE
# ============================================================


def has_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> bool:

    return repository.has_activities_by_stage(
        stage_id,
    )


# ============================================================
# HAS UNFINISHED ACTIVITIES BY STAGE
# ============================================================


def has_unfinished_stage_activities(
    repository: ActivityRepository,
    stage_id: UUID,
) -> bool:

    return repository.has_unfinished_by_stage(
        stage_id,
    )


# ============================================================
# ALL ACTIVITIES FINISHED BY STAGE
# ============================================================


def all_stage_activities_finished(
    repository: ActivityRepository,
    stage_id: UUID,
) -> bool:

    return repository.all_finished_by_stage(
        stage_id,
    )


# ============================================================
# CHECK WHETHER ACTIVITY EXISTS
# ============================================================


def activity_exists(
    repository: ActivityRepository,
    activity_id: UUID,
) -> bool:

    return repository.exists(
        activity_id,
    )