from datetime import timedelta
from uuid import UUID

from app.modules.activity.models import (
    Activity,
    ActivitySource,
    ActivityStatus,
)

from app.modules.activity.repository import (
    ActivityRepository,
)

from app.modules.crop_plan.schemas import (
    CropPlanGenerateRequest,
    CropPlanResponse,
    CropPlanStageResponse,
    CropPlanActivityResponse,
)

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)

from app.modules.crop_stage.repository import (
    CropStageRepository,
)

from app.shared.exceptions import (
    ValidationError,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _get_crop_season(
    activity_repository: ActivityRepository,
    crop_season_id: UUID,
) -> CropSeason:
    """
    Get crop season directly from the database.

    We intentionally do not depend on existing stages or
    activities because a crop season may have zero stages
    and zero activities.
    """

    crop_season = (
        activity_repository.db.query(CropSeason)
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


def _validate_crop_plan_status(
    crop_season: CropSeason,
) -> None:
    """
    Crop plans can only be generated or regenerated
    while the crop season is PLANNED.
    """

    if crop_season.status != CropSeasonStatus.PLANNED:

        raise ValidationError(
            "Crop plan can only be generated while "
            "the crop season is planned."
        )


def _validate_start_date(
    crop_season: CropSeason,
    start_date,
) -> None:
    """
    The generated plan must use the crop season's
    sowing date as its timeline origin.
    """

    if start_date != crop_season.sowing_date:

        raise ValidationError(
            "Crop plan start date must match the "
            "crop season sowing date."
        )


def _validate_stage_requests(
    request: CropPlanGenerateRequest,
) -> None:
    """
    Validate the complete stage structure before
    changing anything in the database.
    """

    if not request.stages:

        raise ValidationError(
            "At least one crop stage is required."
        )

    expected_order = 1

    for stage in request.stages:

        # ----------------------------------------------------
        # Stage order
        # ----------------------------------------------------

        if stage.stage_order != expected_order:

            raise ValidationError(
                "Crop stages must use continuous "
                "stage orders starting from 1."
            )

        # ----------------------------------------------------
        # Timeline
        # ----------------------------------------------------

        if stage.start_day < 1:

            raise ValidationError(
                "Stage start day must be at least 1."
            )

        if stage.end_day < stage.start_day:

            raise ValidationError(
                "Stage end day must be greater than or "
                "equal to start day."
            )

        # ----------------------------------------------------
        # Activities
        # ----------------------------------------------------

        for activity in stage.activities:

            if activity.day < stage.start_day:

                raise ValidationError(
                    f"Activity '{activity.title}' is scheduled "
                    f"before its stage starts."
                )

            if activity.day > stage.end_day:

                raise ValidationError(
                    f"Activity '{activity.title}' is scheduled "
                    f"after its stage ends."
                )

        expected_order += 1


def _calculate_activity_date(
    start_date,
    relative_day: int,
):
    """
    Convert a relative farming day into a calendar date.

    Day 1 = start_date
    Day 2 = start_date + 1 day
    Day 3 = start_date + 2 days
    """

    return start_date + timedelta(
        days=relative_day - 1,
    )


# ============================================================
# BUILD RESPONSE
# ============================================================


def _build_crop_plan_response(
    crop_season: CropSeason,
    stages: list[CropStage],
) -> CropPlanResponse:
    """
    Convert generated database records into the public
    CropPlanResponse.
    """

    stage_responses = []

    total_activities = 0

    for stage in stages:

        activities = sorted(
            stage.activities,
            key=lambda activity: (
                activity.scheduled_date,
                activity.created_at,
            ),
        )

        activity_responses = [
            CropPlanActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ]

        total_activities += len(
            activity_responses,
        )

        stage_responses.append(
            CropPlanStageResponse(
                id=stage.id,
                crop_season_id=stage.crop_season_id,
                name=stage.name,
                description=stage.description,
                stage_order=stage.stage_order,
                start_day=stage.start_day,
                end_day=stage.end_day,
                activities=activity_responses,
            )
        )

    return CropPlanResponse(
        crop_season_id=crop_season.id,
        status=crop_season.status,
        start_date=crop_season.sowing_date,
        stages=stage_responses,
        total_stages=len(stage_responses),
        total_activities=total_activities,
    )


# ============================================================
# GENERATE CROP PLAN
#
# PLANNED
#    ↓
# Generate stages + activities
#
# Existing records:
#
# No destructive replacement is performed here.
#
# This operation is intended for an empty/new plan.
# ============================================================


def generate_crop_plan(
    activity_repository: ActivityRepository,
    crop_season_id: UUID,
    request: CropPlanGenerateRequest,
) -> CropPlanResponse:

    # --------------------------------------------------------
    # Get crop season.
    # --------------------------------------------------------

    crop_season = _get_crop_season(
        activity_repository,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Validate lifecycle.
    # --------------------------------------------------------

    _validate_crop_plan_status(
        crop_season,
    )

    # --------------------------------------------------------
    # Validate timeline.
    # --------------------------------------------------------

    _validate_start_date(
        crop_season,
        request.start_date,
    )

    # --------------------------------------------------------
    # Validate complete request BEFORE modifying DB.
    # --------------------------------------------------------

    _validate_stage_requests(
        request,
    )

    stage_repository = CropStageRepository(
        activity_repository.db,
    )

    # --------------------------------------------------------
    # Do not generate another plan on top of an existing one.
    # --------------------------------------------------------

    existing_stages = (
        stage_repository.get_all_by_crop_season(
            crop_season_id,
        )
    )

    if existing_stages:

        raise ValidationError(
            "A crop plan already exists. "
            "Use regenerate instead."
        )

    try:

        created_stages: list[CropStage] = []

        # ----------------------------------------------------
        # Create stages.
        # ----------------------------------------------------

        for stage_request in request.stages:

            stage = CropStage(
                crop_season_id=crop_season_id,
                name=stage_request.name,
                description=stage_request.description,
                stage_order=stage_request.stage_order,
                start_day=stage_request.start_day,
                end_day=stage_request.end_day,
                status=CropStageStatus.PENDING,
                started_at=None,
                completed_at=None,
            )

            stage_repository.create_without_commit(
                stage,
            )

            created_stages.append(
                stage,
            )

        # ----------------------------------------------------
        # Create activities.
        #
        # Activities are attached to their generated stage.
        # ----------------------------------------------------

        activities: list[Activity] = []

        for stage_request, stage in zip(
            request.stages,
            created_stages,
        ):

            for activity_request in (
                stage_request.activities
            ):

                scheduled_date = (
                    _calculate_activity_date(
                        request.start_date,
                        activity_request.day,
                    )
                )

                activity = Activity(
                    crop_season_id=crop_season_id,
                    stage_id=stage.id,
                    activity_type=(
                        activity_request.activity_type
                    ),
                    title=activity_request.title,
                    description=(
                        activity_request.description
                    ),
                    scheduled_date=scheduled_date,
                    original_scheduled_date=(
                        scheduled_date
                    ),
                    completed_date=None,
                    status=ActivityStatus.PENDING,
                    notes=None,
                    priority=activity_request.priority,
                    estimated_duration_minutes=(
                        activity_request
                        .estimated_duration_minutes
                    ),
                    source=ActivitySource.AI_PLANNED,
                )

                activities.append(
                    activity,
                )

        # ----------------------------------------------------
        # Create all activities.
        # ----------------------------------------------------

        activity_repository.create_many(
            activities,
        )

        # ----------------------------------------------------
        # Commit entire plan as one transaction.
        # ----------------------------------------------------

        activity_repository.commit()

        # ----------------------------------------------------
        # Refresh generated records.
        # ----------------------------------------------------

        for stage in created_stages:

            activity_repository.db.refresh(
                stage,
            )

        for activity in activities:

            activity_repository.refresh(
                activity,
            )

        return _build_crop_plan_response(
            crop_season=crop_season,
            stages=created_stages,
        )

    except Exception:

        activity_repository.rollback()

        raise


# ============================================================
# REGENERATE CROP PLAN
#
# Existing:
#
# Stages
# Activities
#
#       ↓
#
# DELETE
#       ↓
#
# CREATE NEW PLAN
#
# Everything happens inside ONE transaction.
# ============================================================


def regenerate_crop_plan(
    activity_repository: ActivityRepository,
    crop_season_id: UUID,
    request: CropPlanGenerateRequest,
) -> CropPlanResponse:

    # --------------------------------------------------------
    # Get crop season.
    # --------------------------------------------------------

    crop_season = _get_crop_season(
        activity_repository,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Validate lifecycle.
    # --------------------------------------------------------

    _validate_crop_plan_status(
        crop_season,
    )

    # --------------------------------------------------------
    # Validate timeline.
    # --------------------------------------------------------

    _validate_start_date(
        crop_season,
        request.start_date,
    )

    # --------------------------------------------------------
    # Validate request before deleting anything.
    # --------------------------------------------------------

    _validate_stage_requests(
        request,
    )

    stage_repository = CropStageRepository(
        activity_repository.db,
    )

    try:

        # ----------------------------------------------------
        # IMPORTANT ORDER
        #
        # Delete activities FIRST.
        #
        # Then delete stages.
        #
        # This prevents old activities from being detached
        # through ON DELETE SET NULL during regeneration.
        # ----------------------------------------------------

        activity_repository.delete_all_by_crop_season(
            crop_season_id,
        )

        stage_repository.delete_all_by_crop_season(
            crop_season_id,
        )

        # ----------------------------------------------------
        # Create new stages.
        # ----------------------------------------------------

        created_stages: list[CropStage] = []

        for stage_request in request.stages:

            stage = CropStage(
                crop_season_id=crop_season_id,
                name=stage_request.name,
                description=stage_request.description,
                stage_order=stage_request.stage_order,
                start_day=stage_request.start_day,
                end_day=stage_request.end_day,
                status=CropStageStatus.PENDING,
                started_at=None,
                completed_at=None,
            )

            stage_repository.create_without_commit(
                stage,
            )

            created_stages.append(
                stage,
            )

        # ----------------------------------------------------
        # Create new activities.
        # ----------------------------------------------------

        activities: list[Activity] = []

        for stage_request, stage in zip(
            request.stages,
            created_stages,
        ):

            for activity_request in (
                stage_request.activities
            ):

                scheduled_date = (
                    _calculate_activity_date(
                        request.start_date,
                        activity_request.day,
                    )
                )

                activity = Activity(
                    crop_season_id=crop_season_id,
                    stage_id=stage.id,
                    activity_type=(
                        activity_request.activity_type
                    ),
                    title=activity_request.title,
                    description=(
                        activity_request.description
                    ),
                    scheduled_date=scheduled_date,
                    original_scheduled_date=(
                        scheduled_date
                    ),
                    completed_date=None,
                    status=ActivityStatus.PENDING,
                    notes=None,
                    priority=activity_request.priority,
                    estimated_duration_minutes=(
                        activity_request
                        .estimated_duration_minutes
                    ),
                    source=ActivitySource.AI_PLANNED,
                )

                activities.append(
                    activity,
                )

        # ----------------------------------------------------
        # Persist activities.
        # ----------------------------------------------------

        activity_repository.create_many(
            activities,
        )

        # ----------------------------------------------------
        # Commit entire regeneration.
        # ----------------------------------------------------

        activity_repository.commit()

        # ----------------------------------------------------
        # Refresh.
        # ----------------------------------------------------

        for stage in created_stages:

            activity_repository.db.refresh(
                stage,
            )

        for activity in activities:

            activity_repository.refresh(
                activity,
            )

        return _build_crop_plan_response(
            crop_season=crop_season,
            stages=created_stages,
        )

    except Exception:

        activity_repository.rollback()

        raise


# ============================================================
# GET CROP PLAN
# ============================================================


def get_crop_plan(
    activity_repository: ActivityRepository,
    crop_season_id: UUID,
) -> CropPlanResponse:

    # --------------------------------------------------------
    # Get crop season.
    # --------------------------------------------------------

    crop_season = _get_crop_season(
        activity_repository,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Get stages.
    # --------------------------------------------------------

    stage_repository = CropStageRepository(
        activity_repository.db,
    )

    stages = (
        stage_repository.get_all_by_crop_season(
            crop_season_id,
        )
    )

    # --------------------------------------------------------
    # No stages means no generated plan.
    # --------------------------------------------------------

    if not stages:

        raise ValidationError(
            "No crop plan has been generated yet."
        )

    # --------------------------------------------------------
    # Build response.
    # --------------------------------------------------------

    return _build_crop_plan_response(
        crop_season=crop_season,
        stages=stages,
    )