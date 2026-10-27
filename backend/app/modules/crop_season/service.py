from datetime import date
from uuid import UUID

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.farm.models import (
    Farm,
)

from app.modules.crop_season.repository import (
    CropSeasonRepository,
)

from app.modules.crop_season.schemas import (
    CropSeasonCancelRequest,
    CropSeasonCreateRequest,
    CropSeasonHarvestRequest,
    CropSeasonUpdateRequest,
)

from app.modules.crop_stage.models import (
    CropStageStatus,
)

from app.modules.crop_stage.repository import (
    CropStageRepository,
)

from app.shared.exceptions import (
    CropSeasonNotFoundError,
    ValidationError,
)


# ============================================================
# LAND UNIT NORMALIZATION
# ============================================================


def _normalize_land_unit(
    value: str | None,
) -> str:

    normalized = (value or "").strip().lower()

    if normalized in ("hectare", "hectares"):

        return "hectares"

    if normalized in ("acre", "acres"):

        return "acres"

    return normalized


# ============================================================
# CREATE CROP SEASON
# ============================================================


def create_crop_season(
    repository: CropSeasonRepository,
    farm_id: UUID,
    request: CropSeasonCreateRequest,
    farm: Farm | None = None,
) -> CropSeason:

    # --------------------------------------------------------
    # Server-side land allocation validation.
    #
    # Areas are only compared when both use the same unit.
    # --------------------------------------------------------

    if (
        farm is not None
        and farm.land_area > 0
        and _normalize_land_unit(request.land_unit)
        == _normalize_land_unit(farm.land_unit)
        and request.land_area > farm.land_area
    ):

        raise ValidationError(
            "Crop area cannot exceed farm area."
        )

    crop_season = CropSeason(
        farm_id=farm_id,
        crop_name=request.crop_name,
        crop_variety=request.crop_variety,
        season=request.season,
        year=request.year,
        sowing_date=request.sowing_date,
        expected_harvest_date=request.expected_harvest_date,
        land_area=request.land_area,
        land_unit=request.land_unit,
        status=CropSeasonStatus.PLANNED,
        is_active=False,
        harvested_date=None,
        notes=request.notes,
    )

    try:
        return repository.create(crop_season)

    except Exception:
        repository.rollback()
        raise


# ============================================================
# GET CROP SEASON
# ============================================================


def get_crop_season(
    repository: CropSeasonRepository,
    crop_season_id: UUID,
) -> CropSeason:

    crop_season = repository.get_by_id(
        crop_season_id,
    )

    if crop_season is None:
        raise CropSeasonNotFoundError(
            "Crop season not found."
        )

    return crop_season


# ============================================================
# GET ALL CROP SEASONS
# ============================================================


def get_crop_seasons(
    repository: CropSeasonRepository,
    farm_id: UUID,
) -> list[CropSeason]:

    return repository.get_all_by_farm(
        farm_id,
    )


# ============================================================
# GET ACTIVE CROP SEASON
# ============================================================


def get_active_crop_season(
    repository: CropSeasonRepository,
    farm_id: UUID,
) -> CropSeason | None:

    return repository.get_active_by_farm(
        farm_id,
    )


# ============================================================
# GET ALL ACTIVE CROP SEASONS
# ============================================================


def get_active_crop_seasons(
    repository: CropSeasonRepository,
    farm_id: UUID,
) -> list[CropSeason]:

    return repository.get_all_active_by_farm(
        farm_id,
    )


# ============================================================
# GET PLANNED CROP SEASONS
# ============================================================


def get_planned_crop_seasons(
    repository: CropSeasonRepository,
    farm_id: UUID,
) -> list[CropSeason]:

    return repository.get_all_planned_by_farm(
        farm_id,
    )


# ============================================================
# GET HARVESTED CROP SEASONS
# ============================================================


def get_harvested_crop_seasons(
    repository: CropSeasonRepository,
    farm_id: UUID,
) -> list[CropSeason]:

    return repository.get_all_harvested_by_farm(
        farm_id,
    )


# ============================================================
# GET CANCELLED CROP SEASONS
# ============================================================


def get_cancelled_crop_seasons(
    repository: CropSeasonRepository,
    farm_id: UUID,
) -> list[CropSeason]:

    return repository.get_all_cancelled_by_farm(
        farm_id,
    )


# ============================================================
# GET LATEST CROP SEASON
# ============================================================


def get_latest_crop_season(
    repository: CropSeasonRepository,
    farm_id: UUID,
) -> CropSeason | None:

    return repository.get_latest_by_farm(
        farm_id,
    )


# ============================================================
# UPDATE CROP SEASON
#
# Only PLANNED crop seasons can be edited.
# ============================================================


def update_crop_season(
    repository: CropSeasonRepository,
    crop_season: CropSeason,
    request: CropSeasonUpdateRequest,
    stage_repository: CropStageRepository | None = None,
) -> CropSeason:

    if crop_season.status != CropSeasonStatus.PLANNED:
        raise ValidationError(
            "Only a planned crop season can be edited."
        )

    update_data = request.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        return crop_season

    # --------------------------------------------------------
    # A generated plan stores activity dates derived from the
    # crop timeline. Only notes may change after that point.
    # --------------------------------------------------------

    if stage_repository is not None:

        stages = stage_repository.get_all_by_crop_season(
            crop_season.id,
        )

        if stages and set(update_data) - {"notes"}:
            raise ValidationError(
                "Crop details cannot be edited after a crop "
                "plan has been generated."
            )

    # --------------------------------------------------------
    # Calculate final timeline.
    # --------------------------------------------------------

    final_sowing_date = update_data.get(
        "sowing_date",
        crop_season.sowing_date,
    )

    final_expected_harvest_date = update_data.get(
        "expected_harvest_date",
        crop_season.expected_harvest_date,
    )

    # --------------------------------------------------------
    # Validate final timeline.
    # --------------------------------------------------------

    if (
        final_expected_harvest_date is not None
        and final_expected_harvest_date < final_sowing_date
    ):
        raise ValidationError(
            "Expected harvest date must be greater than "
            "or equal to sowing date."
        )

    # --------------------------------------------------------
    # Keep year synchronized with sowing date.
    # --------------------------------------------------------

    if (
        "sowing_date" in update_data
        and "year" not in update_data
    ):
        update_data["year"] = final_sowing_date.year

    # --------------------------------------------------------
    # Apply changes.
    # --------------------------------------------------------

    for field, value in update_data.items():
        setattr(
            crop_season,
            field,
            value,
        )

    # --------------------------------------------------------
    # Planned state must remain synchronized.
    # --------------------------------------------------------

    crop_season.status = CropSeasonStatus.PLANNED
    crop_season.is_active = False
    crop_season.harvested_date = None

    try:
        return repository.update(
            crop_season,
        )

    except Exception:
        repository.rollback()
        raise


# ============================================================
# ACTIVATE CROP SEASON
#
# PLANNED
#     ↓
# ACTIVE
#
# Also activates first crop stage.
# ============================================================


def activate_crop_season(
    repository: CropSeasonRepository,
    stage_repository: CropStageRepository,
    crop_season: CropSeason,
) -> CropSeason:

    # --------------------------------------------------------
    # Already active.
    #
    # Idempotent behavior.
    # --------------------------------------------------------

    if crop_season.status == CropSeasonStatus.ACTIVE:

        if not crop_season.is_active:

            try:
                crop_season.is_active = True

                repository.flush()
                repository.commit()

                repository.refresh(
                    crop_season,
                )

            except Exception:
                repository.rollback()
                raise

        return crop_season

    # --------------------------------------------------------
    # Only planned crop can start.
    # --------------------------------------------------------

    if crop_season.status != CropSeasonStatus.PLANNED:
        raise ValidationError(
            "Only a planned crop season can be activated."
        )

    # --------------------------------------------------------
    # Only one active crop per farm.
    #
    # Lock the farm row so concurrent activation attempts
    # cannot both pass the check.
    # --------------------------------------------------------

    repository.lock_farm(
        crop_season.farm_id,
    )

    active_crop = repository.get_active_by_farm(
        crop_season.farm_id,
    )

    if (
        active_crop is not None
        and active_crop.id != crop_season.id
    ):
        raise ValidationError(
            "Another crop season is already active "
            "for this farm. Complete or cancel it first."
        )

    # --------------------------------------------------------
    # Get first pending stage.
    # --------------------------------------------------------

    first_stage = (
        stage_repository.get_first_pending_stage(
            crop_season.id,
        )
    )

    if first_stage is None:
        raise ValidationError(
            "Crop plan has not been generated yet. "
            "Generate the crop plan before starting farming."
        )

    # --------------------------------------------------------
    # Verify ownership.
    # --------------------------------------------------------

    if first_stage.crop_season_id != crop_season.id:
        raise ValidationError(
            "The first crop stage does not belong "
            "to this crop season."
        )

    # --------------------------------------------------------
    # First stage must be stage 1.
    # --------------------------------------------------------

    if first_stage.stage_order != 1:
        raise ValidationError(
            "Crop plan must start with stage order 1."
        )

    # --------------------------------------------------------
    # First stage must be pending.
    # --------------------------------------------------------

    if first_stage.status != CropStageStatus.PENDING:
        raise ValidationError(
            "The first crop stage is not available "
            "for activation."
        )

    # --------------------------------------------------------
    # No other active stage.
    # --------------------------------------------------------

    active_stage = (
        stage_repository.get_active_by_crop_season(
            crop_season.id,
        )
    )

    if active_stage is not None:
        raise ValidationError(
            "This crop season already has an active stage."
        )

    try:

        # ----------------------------------------------------
        # Activate crop.
        # ----------------------------------------------------

        repository.mark_active(
            crop_season,
        )

        # ----------------------------------------------------
        # Activate first stage.
        # ----------------------------------------------------

        first_stage.status = CropStageStatus.ACTIVE

        first_stage.started_at = (
            crop_season.sowing_date
        )

        first_stage.completed_at = None

        # ----------------------------------------------------
        # Flush.
        # ----------------------------------------------------

        repository.flush()

        # ----------------------------------------------------
        # Commit.
        # ----------------------------------------------------

        repository.commit()

        # ----------------------------------------------------
        # Refresh.
        # ----------------------------------------------------

        repository.refresh(
            crop_season,
        )

        stage_repository.refresh(
            first_stage,
        )

    except Exception:
        repository.rollback()
        raise

    return crop_season


# ============================================================
# CAN COMPLETE CROP SEASON
# ============================================================


def can_complete_crop_season(
    stage_repository: CropStageRepository,
    crop_season: CropSeason,
) -> bool:

    # --------------------------------------------------------
    # Must be active.
    # --------------------------------------------------------

    if crop_season.status != CropSeasonStatus.ACTIVE:
        return False

    # --------------------------------------------------------
    # No active stage.
    # --------------------------------------------------------

    active_stage = (
        stage_repository.get_active_by_crop_season(
            crop_season.id,
        )
    )

    if active_stage is not None:
        return False

    # --------------------------------------------------------
    # All stages must be finished.
    #
    # COMPLETED + SKIPPED = FINISHED
    # --------------------------------------------------------

    return stage_repository.all_finished(
        crop_season.id,
    )


# ============================================================
# COMPLETE / HARVEST CROP SEASON
#
# ACTIVE
#     ↓
# HARVESTED
# ============================================================


def complete_crop_season(
    repository: CropSeasonRepository,
    stage_repository: CropStageRepository,
    crop_season: CropSeason,
    request: CropSeasonHarvestRequest | None = None,
) -> CropSeason:

    # --------------------------------------------------------
    # Only active crop can be harvested.
    # --------------------------------------------------------

    if crop_season.status != CropSeasonStatus.ACTIVE:
        raise ValidationError(
            "Only an active crop season can be harvested."
        )

    # --------------------------------------------------------
    # Check active stage.
    # --------------------------------------------------------

    active_stage = (
        stage_repository.get_active_by_crop_season(
            crop_season.id,
        )
    )

    if active_stage is not None:
        raise ValidationError(
            "The current crop stage must be completed "
            "or skipped before harvesting the crop."
        )

    # --------------------------------------------------------
    # Check all stages.
    # --------------------------------------------------------

    if not stage_repository.all_finished(
        crop_season.id,
    ):
        raise ValidationError(
            "All crop stages must be completed or skipped "
            "before harvesting."
        )

    # --------------------------------------------------------
    # Determine harvest date.
    # --------------------------------------------------------

    harvested_date = (
        request.harvested_date
        if request is not None
        and request.harvested_date is not None
        else date.today()
    )

    # --------------------------------------------------------
    # Harvest date cannot be before sowing date.
    # --------------------------------------------------------

    if harvested_date < crop_season.sowing_date:
        raise ValidationError(
            "Harvested date cannot be before sowing date."
        )

    try:

        # ----------------------------------------------------
        # ACTIVE → HARVESTED
        # ----------------------------------------------------

        repository.mark_harvested(
            crop_season,
        )

        # ----------------------------------------------------
        # Store actual harvest date.
        # ----------------------------------------------------

        crop_season.harvested_date = harvested_date

        # ----------------------------------------------------
        # Optional harvest notes.
        # ----------------------------------------------------

        if (
            request is not None
            and request.notes is not None
        ):
            crop_season.notes = request.notes

        # ----------------------------------------------------
        # Flush.
        # ----------------------------------------------------

        repository.flush()

        # ----------------------------------------------------
        # Commit.
        # ----------------------------------------------------

        repository.commit()

        # ----------------------------------------------------
        # Refresh.
        # ----------------------------------------------------

        repository.refresh(
            crop_season,
        )

    except Exception:
        repository.rollback()
        raise

    return crop_season


# ============================================================
# CANCEL CROP SEASON
#
# PLANNED / ACTIVE
#       ↓
# CANCELLED
# ============================================================


def cancel_crop_season(
    repository: CropSeasonRepository,
    crop_season: CropSeason,
    request: CropSeasonCancelRequest | None = None,
    stage_repository: CropStageRepository | None = None,
) -> CropSeason:

    # --------------------------------------------------------
    # Harvested crop cannot be cancelled.
    # --------------------------------------------------------

    if crop_season.status == CropSeasonStatus.HARVESTED:
        raise ValidationError(
            "Harvested crop season cannot be cancelled."
        )

    # --------------------------------------------------------
    # Already cancelled.
    #
    # Idempotent behavior.
    # --------------------------------------------------------

    if crop_season.status == CropSeasonStatus.CANCELLED:
        return crop_season

    # --------------------------------------------------------
    # Only planned / active can be cancelled.
    # --------------------------------------------------------

    if crop_season.status not in (
        CropSeasonStatus.PLANNED,
        CropSeasonStatus.ACTIVE,
    ):
        raise ValidationError(
            "Only a planned or active crop season "
            "can be cancelled."
        )

    try:

        repository.mark_cancelled(
            crop_season,
        )

        if (
            request is not None
            and request.reason is not None
        ):
            crop_season.cancellation_reason = (
                request.reason
            )

        if stage_repository is not None:

            active_stage = (
                stage_repository.get_active_by_crop_season(
                    crop_season.id,
                )
            )

            if active_stage is not None:

                active_stage.status = CropStageStatus.SKIPPED
                active_stage.completed_at = date.today()

        repository.commit()

        repository.refresh(
            crop_season,
        )

    except Exception:
        repository.rollback()
        raise

    return crop_season


# ============================================================
# DELETE CROP SEASON
#
# PLANNED / CANCELLED
#       ↓
#     DELETE
#
# ACTIVE / HARVESTED
#       X
# ============================================================


def delete_crop_season(
    repository: CropSeasonRepository,
    crop_season: CropSeason,
) -> None:

    # --------------------------------------------------------
    # Active crop cannot be deleted.
    # --------------------------------------------------------

    if crop_season.status == CropSeasonStatus.ACTIVE:
        raise ValidationError(
            "Active crop season cannot be deleted. "
            "Cancel it first."
        )

    # --------------------------------------------------------
    # Harvested history is permanent.
    # --------------------------------------------------------

    if crop_season.status == CropSeasonStatus.HARVESTED:
        raise ValidationError(
            "Harvested crop season cannot be deleted."
        )

    # --------------------------------------------------------
    # Only planned / cancelled can be deleted.
    # --------------------------------------------------------

    if crop_season.status not in (
        CropSeasonStatus.PLANNED,
        CropSeasonStatus.CANCELLED,
    ):
        raise ValidationError(
            "Crop season cannot be deleted in its "
            "current state."
        )

    try:

        repository.delete(
            crop_season,
        )

    except Exception:
        repository.rollback()
        raise