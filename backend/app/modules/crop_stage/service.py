from datetime import date
from uuid import UUID

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)

from app.modules.activity.models import (
    Activity,
    ActivityStatus,
)

from app.modules.crop_stage.repository import (
    CropStageRepository,
)

from app.modules.crop_stage.schemas import (
    CropStageCreateRequest,
    CropStageUpdateRequest,
)

from app.shared.exceptions import (
    ValidationError,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _get_crop_season_for_stage(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> CropSeason:

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


# ============================================================
# VALIDATE STAGE TIMELINE
# ============================================================


def _validate_stage_timeline(
    start_day: int,
    end_day: int,
) -> None:

    if start_day < 1:

        raise ValidationError(
            "Stage start day must be at least 1."
        )

    if end_day < 1:

        raise ValidationError(
            "Stage end day must be at least 1."
        )

    if end_day < start_day:

        raise ValidationError(
            "End day must be greater than or equal "
            "to start day."
        )


# ============================================================
# VALIDATE STAGE ORDER
# ============================================================


def _validate_stage_order(
    stage_order: int,
) -> None:

    if stage_order < 1:

        raise ValidationError(
            "Stage order must be at least 1."
        )


# ============================================================
# VALIDATE STAGE SEQUENCE
# ============================================================


def _validate_stage_sequence(
    stages: list[CropStage],
) -> None:

    if not stages:
        return

    ordered_stages = sorted(
        stages,
        key=lambda stage: stage.stage_order,
    )

    expected_order = 1

    for stage in ordered_stages:

        if stage.stage_order != expected_order:

            raise ValidationError(
                "Crop stages must use continuous "
                "stage orders starting from 1."
            )

        expected_order += 1


# ============================================================
# GET EXPECTED NEXT STAGE ORDER
# ============================================================


def _get_expected_next_stage_order(
    stages: list[CropStage],
) -> int:

    if not stages:
        return 1

    _validate_stage_sequence(
        stages,
    )

    return len(stages) + 1


# ============================================================
# VALIDATE CURRENT ACTIVE STAGE
# ============================================================


def _validate_current_active_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> None:

    active_stage = (
        repository.get_active_by_crop_season(
            stage.crop_season_id,
        )
    )

    if active_stage is None:

        raise ValidationError(
            "No active crop stage exists."
        )

    if active_stage.id != stage.id:

        raise ValidationError(
            "This is not the current active crop stage."
        )


# ============================================================
# GET NEXT PENDING STAGE
# ============================================================


def _get_next_pending_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> CropStage | None:

    return repository.get_next_pending_stage(
        crop_season_id=stage.crop_season_id,
        current_stage_order=stage.stage_order,
    )


# ============================================================
# ACTIVATE NEXT STAGE
# ============================================================


def _activate_next_stage_if_available(
    repository: CropStageRepository,
    stage: CropStage,
) -> CropStage | None:

    next_stage = _get_next_pending_stage(
        repository,
        stage,
    )

    # --------------------------------------------------------
    # No next stage.
    #
    # Current stage was the final stage.
    # --------------------------------------------------------

    if next_stage is None:

        return None

    # --------------------------------------------------------
    # Stages must be sequential.
    # --------------------------------------------------------

    if next_stage.stage_order != stage.stage_order + 1:

        raise ValidationError(
            "Crop stage sequence is invalid. "
            "The next stage must immediately follow "
            "the current stage."
        )

    # --------------------------------------------------------
    # Only another ACTIVE stage is an error.
    #
    # Exclude the current stage because complete_stage()
    # has already changed it to COMPLETED/SKIPPED.
    #
    # This also prevents stale-session/autoflush issues.
    # --------------------------------------------------------

    active_stage = (
        repository.db.query(CropStage)
        .filter(
            CropStage.crop_season_id == stage.crop_season_id,
            CropStage.status == CropStageStatus.ACTIVE,
            CropStage.id != stage.id,
        )
        .first()
    )

    if active_stage is not None:

        raise ValidationError(
            "Another crop stage is already active."
        )

    # --------------------------------------------------------
    # Next stage must actually be PENDING.
    # --------------------------------------------------------

    if next_stage.status != CropStageStatus.PENDING:

        raise ValidationError(
            "The next crop stage is not pending."
        )

    # --------------------------------------------------------
    # PENDING → ACTIVE
    # --------------------------------------------------------

    next_stage.status = CropStageStatus.ACTIVE

    next_stage.started_at = date.today()

    next_stage.completed_at = None

    return next_stage


# ============================================================
# CREATE STAGE
# ============================================================


def create_stage(
    repository: CropStageRepository,
    crop_season_id: UUID,
    request: CropStageCreateRequest,
) -> CropStage:

    crop_season = _get_crop_season_for_stage(
        repository,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Crop plan can only be modified while PLANNED.
    # --------------------------------------------------------

    if crop_season.status != CropSeasonStatus.PLANNED:

        raise ValidationError(
            "Crop stages can only be created before "
            "farming starts."
        )

    _validate_stage_order(
        request.stage_order,
    )

    _validate_stage_timeline(
        start_day=request.start_day,
        end_day=request.end_day,
    )

    existing_stages = (
        repository.get_all_by_crop_season(
            crop_season_id,
        )
    )

    _validate_stage_sequence(
        existing_stages,
    )

    expected_order = _get_expected_next_stage_order(
        existing_stages,
    )

    if request.stage_order != expected_order:

        raise ValidationError(
            f"Next crop stage must have "
            f"stage order {expected_order}."
        )

    stage = CropStage(
        crop_season_id=crop_season_id,
        name=request.name,
        description=request.description,
        stage_order=request.stage_order,
        start_day=request.start_day,
        end_day=request.end_day,
        status=CropStageStatus.PENDING,
        started_at=None,
        completed_at=None,
    )

    try:

        return repository.create(
            stage,
        )

    except Exception:

        repository.rollback()

        raise


# ============================================================
# GET STAGE
# ============================================================


def get_stage(
    repository: CropStageRepository,
    stage_id: UUID,
) -> CropStage:

    stage = repository.get_by_id(
        stage_id,
    )

    if stage is None:

        raise ValidationError(
            "Crop stage not found."
        )

    return stage


# ============================================================
# GET ALL STAGES
# ============================================================


def get_crop_stages(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> list[CropStage]:

    return repository.get_all_by_crop_season(
        crop_season_id,
    )


# ============================================================
# GET ACTIVE STAGE
# ============================================================


def get_active_stage(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> CropStage | None:

    return repository.get_active_by_crop_season(
        crop_season_id,
    )


# ============================================================
# GET PENDING STAGES
# ============================================================


def get_pending_stages(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> list[CropStage]:

    return repository.get_pending_by_crop_season(
        crop_season_id,
    )


# ============================================================
# GET COMPLETED STAGES
# ============================================================


def get_completed_stages(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> list[CropStage]:

    return repository.get_completed_by_crop_season(
        crop_season_id,
    )


# ============================================================
# GET SKIPPED STAGES
# ============================================================


def get_skipped_stages(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> list[CropStage]:

    return repository.get_skipped_by_crop_season(
        crop_season_id,
    )


# ============================================================
# UPDATE STAGE
# ============================================================


def update_stage(
    repository: CropStageRepository,
    stage: CropStage,
    request: CropStageUpdateRequest,
) -> CropStage:

    # --------------------------------------------------------
    # Crop must be PLANNED.
    # --------------------------------------------------------

    if stage.crop_season.status != CropSeasonStatus.PLANNED:

        raise ValidationError(
            "Crop stages can only be edited before "
            "farming starts."
        )

    # --------------------------------------------------------
    # Stage must be PENDING.
    # --------------------------------------------------------

    if stage.status != CropStageStatus.PENDING:

        raise ValidationError(
            "Only pending crop stages can be edited."
        )

    update_data = request.model_dump(
        exclude_unset=True,
    )

    if not update_data:

        return stage

    # --------------------------------------------------------
    # Validate final timeline.
    # --------------------------------------------------------

    start_day = update_data.get(
        "start_day",
        stage.start_day,
    )

    end_day = update_data.get(
        "end_day",
        stage.end_day,
    )

    _validate_stage_timeline(
        start_day=start_day,
        end_day=end_day,
    )

    # --------------------------------------------------------
    # Stage order cannot change.
    # --------------------------------------------------------

    requested_order = update_data.get(
        "stage_order",
        stage.stage_order,
    )

    _validate_stage_order(
        requested_order,
    )

    if requested_order != stage.stage_order:

        raise ValidationError(
            "Stage order cannot be changed after "
            "the crop stage has been created."
        )

    # --------------------------------------------------------
    # Apply allowed changes.
    # --------------------------------------------------------

    for field, value in update_data.items():

        setattr(
            stage,
            field,
            value,
        )

    # --------------------------------------------------------
    # Lifecycle remains unchanged.
    # --------------------------------------------------------

    stage.status = CropStageStatus.PENDING
    stage.started_at = None
    stage.completed_at = None

    return repository.update(
        stage,
    )


# ============================================================
# ACTIVATE FIRST STAGE
# ============================================================


def activate_first_stage(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> CropStage:

    crop_season = _get_crop_season_for_stage(
        repository,
        crop_season_id,
    )

    if crop_season.status != CropSeasonStatus.ACTIVE:

        raise ValidationError(
            "Crop farming must be active before "
            "activating a stage."
        )

    active_stage = (
        repository.get_active_by_crop_season(
            crop_season_id,
        )
    )

    if active_stage is not None:

        return active_stage

    first_stage = (
        repository.get_first_pending_stage(
            crop_season_id,
        )
    )

    if first_stage is None:

        raise ValidationError(
            "No pending crop stages are available."
        )

    if first_stage.stage_order != 1:

        raise ValidationError(
            "Crop plan must start with stage order 1."
        )

    first_stage.status = CropStageStatus.ACTIVE

    first_stage.started_at = crop_season.sowing_date

    first_stage.completed_at = None

    try:

        repository.flush()

        repository.commit()

        repository.refresh(
            first_stage,
        )

    except Exception:

        repository.rollback()

        raise

    return first_stage


# ============================================================
# ACTIVATE STAGE
# ============================================================


def activate_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> CropStage:

    # --------------------------------------------------------
    # Crop must be ACTIVE.
    # --------------------------------------------------------

    if stage.crop_season.status != CropSeasonStatus.ACTIVE:

        raise ValidationError(
            "Crop farming must be active before "
            "activating a stage."
        )

    # --------------------------------------------------------
    # Idempotent if already active.
    # --------------------------------------------------------

    if stage.status == CropStageStatus.ACTIVE:

        return stage

    # --------------------------------------------------------
    # Completed cannot restart.
    # --------------------------------------------------------

    if stage.status == CropStageStatus.COMPLETED:

        raise ValidationError(
            "Completed crop stage cannot be activated again."
        )

    # --------------------------------------------------------
    # Skipped cannot restart.
    # --------------------------------------------------------

    if stage.status == CropStageStatus.SKIPPED:

        raise ValidationError(
            "Skipped crop stage cannot be activated again."
        )

    # --------------------------------------------------------
    # Only PENDING can become ACTIVE.
    # --------------------------------------------------------

    if stage.status != CropStageStatus.PENDING:

        raise ValidationError(
            "Only a pending crop stage can be activated."
        )

    # --------------------------------------------------------
    # Only one ACTIVE stage.
    # --------------------------------------------------------

    active_stage = (
        repository.get_active_by_crop_season(
            stage.crop_season_id,
        )
    )

    if (
        active_stage is not None
        and active_stage.id != stage.id
    ):

        raise ValidationError(
            "Another crop stage is already active."
        )

    # --------------------------------------------------------
    # Get first pending stage.
    # --------------------------------------------------------

    first_pending_stage = (
        repository.get_first_pending_stage(
            stage.crop_season_id,
        )
    )

    if first_pending_stage is None:

        raise ValidationError(
            "No pending crop stages are available."
        )

    # --------------------------------------------------------
    # Stages must execute sequentially.
    # --------------------------------------------------------

    if first_pending_stage.id != stage.id:

        raise ValidationError(
            "Stages must be completed in order. "
            "Complete or skip the previous stage first."
        )

    # --------------------------------------------------------
    # PENDING → ACTIVE
    # --------------------------------------------------------

    stage.status = CropStageStatus.ACTIVE

    stage.started_at = date.today()

    stage.completed_at = None

    try:

        repository.flush()

        repository.commit()

        repository.refresh(
            stage,
        )

    except Exception:

        repository.rollback()

        raise

    return stage


# ============================================================
# COMPLETE STAGE
# ============================================================


def complete_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> CropStage:

    # --------------------------------------------------------
    # Crop must be ACTIVE.
    # --------------------------------------------------------

    if stage.crop_season.status != CropSeasonStatus.ACTIVE:

        raise ValidationError(
            "Crop season is not currently active."
        )

    # --------------------------------------------------------
    # Only ACTIVE stage can be completed.
    # --------------------------------------------------------

    if stage.status != CropStageStatus.ACTIVE:

        raise ValidationError(
            "Only an active crop stage can be completed."
        )

    _validate_current_active_stage(
        repository,
        stage,
    )

    # --------------------------------------------------------
    # ALL ACTIVITIES MUST BE FINISHED
    #
    # COMPLETED = finished
    # SKIPPED    = finished
    # PENDING    = unfinished
    # IN_PROGRESS = unfinished
    # --------------------------------------------------------

    unfinished_activities = (
        repository.db.query(Activity)
        .filter(
            Activity.stage_id == stage.id,
            Activity.status.notin_(
                [
                    ActivityStatus.COMPLETED,
                    ActivityStatus.SKIPPED,
                ]
            ),
        )
        .count()
    )

    if unfinished_activities > 0:

        raise ValidationError(
            "All activities must be completed or skipped "
            "before completing the crop stage."
        )

    try:

        # ----------------------------------------------------
        # ACTIVE → COMPLETED
        # ----------------------------------------------------

        stage.status = CropStageStatus.COMPLETED

        stage.completed_at = date.today()

        # ----------------------------------------------------
        # Automatically activate next stage.
        # ----------------------------------------------------

        next_stage = _activate_next_stage_if_available(
            repository,
            stage,
        )

        # ----------------------------------------------------
        # Commit both operations together.
        # ----------------------------------------------------

        repository.flush()

        repository.commit()

        repository.refresh(
            stage,
        )

        if next_stage is not None:

            repository.refresh(
                next_stage,
            )

    except Exception:

        repository.rollback()

        raise

    return stage


# ============================================================
# SKIP STAGE
# ============================================================


def skip_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> CropStage:

    # --------------------------------------------------------
    # Crop must be ACTIVE.
    # --------------------------------------------------------

    if stage.crop_season.status != CropSeasonStatus.ACTIVE:

        raise ValidationError(
            "Crop season is not currently active."
        )

    # --------------------------------------------------------
    # Already skipped.
    # --------------------------------------------------------

    if stage.status == CropStageStatus.SKIPPED:

        return stage

    # --------------------------------------------------------
    # Completed cannot be skipped.
    # --------------------------------------------------------

    if stage.status == CropStageStatus.COMPLETED:

        raise ValidationError(
            "Completed crop stage cannot be skipped."
        )

    # --------------------------------------------------------
    # Only ACTIVE stage can be skipped.
    # --------------------------------------------------------

    if stage.status != CropStageStatus.ACTIVE:

        raise ValidationError(
            "Only the active crop stage can be skipped."
        )

    _validate_current_active_stage(
        repository,
        stage,
    )

    try:

        # ----------------------------------------------------
        # ACTIVE → SKIPPED
        # ----------------------------------------------------

        stage.status = CropStageStatus.SKIPPED

        stage.completed_at = date.today()

        # ----------------------------------------------------
        # Automatically activate next stage.
        # ----------------------------------------------------

        next_stage = _activate_next_stage_if_available(
            repository,
            stage,
        )

        # ----------------------------------------------------
        # Commit both operations together.
        # ----------------------------------------------------

        repository.flush()

        repository.commit()

        repository.refresh(
            stage,
        )

        if next_stage is not None:

            repository.refresh(
                next_stage,
            )

    except Exception:

        repository.rollback()

        raise

    return stage


# ============================================================
# ACTIVATE NEXT STAGE
# ============================================================


def activate_next_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> CropStage | None:

    # --------------------------------------------------------
    # Crop must be ACTIVE.
    # --------------------------------------------------------

    if stage.crop_season.status != CropSeasonStatus.ACTIVE:

        raise ValidationError(
            "Crop season is not currently active."
        )

    # --------------------------------------------------------
    # Current stage must be finished.
    # --------------------------------------------------------

    if stage.status not in (
        CropStageStatus.COMPLETED,
        CropStageStatus.SKIPPED,
    ):

        raise ValidationError(
            "Current stage must be completed or skipped "
            "before activating the next stage."
        )

    # --------------------------------------------------------
    # There must not already be an active stage.
    # --------------------------------------------------------

    active_stage = (
        repository.get_active_by_crop_season(
            stage.crop_season_id,
        )
    )

    if active_stage is not None:

        raise ValidationError(
            "Another crop stage is already active."
        )

    try:

        next_stage = _activate_next_stage_if_available(
            repository,
            stage,
        )

        # ----------------------------------------------------
        # No next stage means crop is ready for harvest.
        # ----------------------------------------------------

        if next_stage is None:

            return None

        repository.flush()

        repository.commit()

        repository.refresh(
            next_stage,
        )

        return next_stage

    except Exception:

        repository.rollback()

        raise


# ============================================================
# GET NEXT STAGE
# ============================================================


def get_next_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> CropStage | None:

    return repository.get_next_stage(
        crop_season_id=stage.crop_season_id,
        current_stage_order=stage.stage_order,
    )


# ============================================================
# CHECK WHETHER ALL STAGES ARE FINISHED
# ============================================================


def all_stages_completed(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> bool:

    total_stages = (
        repository.count_by_crop_season(
            crop_season_id,
        )
    )

    if total_stages == 0:

        return False

    return repository.all_finished(
        crop_season_id,
    )


# ============================================================
# DELETE STAGE
# ============================================================


def delete_stage(
    repository: CropStageRepository,
    stage: CropStage,
) -> None:

    # --------------------------------------------------------
    # Crop must be PLANNED.
    # --------------------------------------------------------

    if stage.crop_season.status != CropSeasonStatus.PLANNED:

        raise ValidationError(
            "Crop stages cannot be deleted after "
            "farming starts."
        )

    # --------------------------------------------------------
    # Stage must be PENDING.
    # --------------------------------------------------------

    if stage.status != CropStageStatus.PENDING:

        raise ValidationError(
            "Only pending crop stages can be deleted."
        )

    # --------------------------------------------------------
    # Validate sequence.
    # --------------------------------------------------------

    stages = (
        repository.get_all_by_crop_season(
            stage.crop_season_id,
        )
    )

    _validate_stage_sequence(
        stages,
    )

    # --------------------------------------------------------
    # Only last stage can be deleted.
    # --------------------------------------------------------

    last_stage = repository.get_last_stage(
        stage.crop_season_id,
    )

    if last_stage is None:

        raise ValidationError(
            "Crop stage not found."
        )

    if last_stage.id != stage.id:

        raise ValidationError(
            "Only the last crop stage can be deleted."
        )

    repository.delete(
        stage,
    )


# ============================================================
# DELETE ALL STAGES
# ============================================================


def delete_all_stages(
    repository: CropStageRepository,
    crop_season_id: UUID,
) -> None:

    crop_season = _get_crop_season_for_stage(
        repository,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Only PLANNED crops can regenerate.
    # --------------------------------------------------------

    if crop_season.status != CropSeasonStatus.PLANNED:

        raise ValidationError(
            "Crop plan can only be regenerated before "
            "farming starts."
        )

    stages = (
        repository.get_all_by_crop_season(
            crop_season_id,
        )
    )

    if not stages:

        return

    _validate_stage_sequence(
        stages,
    )

    repository.delete_all_by_crop_season(
        crop_season_id,
    )