from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User

from app.modules.farmer.repository import (
    FarmerRepository,
)

from app.modules.crop_season.repository import (
    CropSeasonRepository,
)

from app.modules.crop_season.models import (
    CropSeasonStatus,
)

from app.modules.crop_stage.repository import (
    CropStageRepository,
)

from app.modules.crop_stage.schemas import (
    CropStageCreateRequest,
    CropStageUpdateRequest,
    CropStageResponse,
)

from app.modules.crop_stage.service import (
    create_stage,
    get_stage,
    get_crop_stages,
    get_active_stage,
    get_pending_stages,
    get_completed_stages,
    get_skipped_stages,
    get_next_stage,
    update_stage,
    activate_stage,
    complete_stage,
    skip_stage,
    all_stages_completed,
    delete_stage,
)

from app.shared.responses import ApiResponse


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/crop-stages",
    tags=["Crop Stage"],
)


# ============================================================
# PRIVATE HELPERS
# ============================================================


def _get_farmer(
    db: Session,
    current_user: User,
):
    """
    Get farmer profile belonging to authenticated user.
    """

    farmer_repository = FarmerRepository(db)

    farmer = farmer_repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found.",
        )

    return farmer


def _get_crop_season(
    db: Session,
    crop_season_id: UUID,
):
    """
    Get crop season by ID.
    """

    repository = CropSeasonRepository(db)

    crop = repository.get_by_id(
        crop_season_id,
    )

    if crop is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop season not found.",
        )

    return crop


def _verify_crop_access(
    crop,
    farmer,
) -> None:
    """
    Ensure crop season belongs to authenticated farmer.
    """

    if crop.farm.farmer_id != farmer.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


def _get_stage(
    db: Session,
    stage_id: UUID,
):
    """
    Get crop stage by ID.
    """

    repository = CropStageRepository(db)

    try:

        return get_stage(
            repository=repository,
            stage_id=stage_id,
        )

    except Exception as exc:

        # Service currently raises ValidationError
        # for missing stage.
        #
        # Keep API-level response as 404.

        from app.shared.exceptions import ValidationError

        if isinstance(exc, ValidationError):

            if str(exc) == "Crop stage not found.":

                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Crop stage not found.",
                )

        raise


def _verify_stage_access(
    stage,
    farmer,
) -> None:
    """
    Ensure stage belongs to a crop season owned
    by authenticated farmer.
    """

    if stage.crop_season.farm.farmer_id != farmer.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


# ============================================================
# CREATE STAGE
#
# POST /crop-stages?crop_season_id=...
#
# CropSeason:
#
# PLANNED
#
# New Stage:
#
# PENDING
# ============================================================


@router.post(
    "",
    response_model=ApiResponse[CropStageResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_crop_stage_endpoint(
    crop_season_id: UUID,
    request: CropStageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    _verify_crop_access(
        crop,
        farmer,
    )

    if crop.status != CropSeasonStatus.PLANNED:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Crop stages can only be created "
                "before farming starts."
            ),
        )

    repository = CropStageRepository(db)

    stage = create_stage(
        repository=repository,
        crop_season_id=crop.id,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Crop stage created successfully.",
        data=CropStageResponse.model_validate(
            stage,
        ),
    )


# ============================================================
# LIST ALL STAGES
#
# GET /crop-stages?crop_season_id=...
# ============================================================


@router.get(
    "",
    response_model=ApiResponse[list[CropStageResponse]],
)
def list_crop_stages_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    _verify_crop_access(
        crop,
        farmer,
    )

    repository = CropStageRepository(db)

    stages = get_crop_stages(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Crop stages retrieved successfully.",
        data=[
            CropStageResponse.model_validate(
                stage,
            )
            for stage in stages
        ],
    )


# ============================================================
# GET ACTIVE STAGE
#
# GET /crop-stages/active?crop_season_id=...
#
# Returns:
#
# ACTIVE stage
# or
# null
# ============================================================


@router.get(
    "/active",
    response_model=ApiResponse[CropStageResponse | None],
)
def get_active_crop_stage_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    _verify_crop_access(
        crop,
        farmer,
    )

    repository = CropStageRepository(db)

    stage = get_active_stage(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Active crop stage retrieved successfully.",
        data=(
            CropStageResponse.model_validate(
                stage,
            )
            if stage is not None
            else None
        ),
    )


# ============================================================
# GET PENDING STAGES
#
# GET /crop-stages/pending?crop_season_id=...
# ============================================================


@router.get(
    "/pending",
    response_model=ApiResponse[list[CropStageResponse]],
)
def get_pending_crop_stages_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    _verify_crop_access(
        crop,
        farmer,
    )

    repository = CropStageRepository(db)

    stages = get_pending_stages(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Pending crop stages retrieved successfully.",
        data=[
            CropStageResponse.model_validate(
                stage,
            )
            for stage in stages
        ],
    )


# ============================================================
# GET COMPLETED STAGES
#
# GET /crop-stages/completed?crop_season_id=...
# ============================================================


@router.get(
    "/completed",
    response_model=ApiResponse[list[CropStageResponse]],
)
def get_completed_crop_stages_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    _verify_crop_access(
        crop,
        farmer,
    )

    repository = CropStageRepository(db)

    stages = get_completed_stages(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Completed crop stages retrieved successfully.",
        data=[
            CropStageResponse.model_validate(
                stage,
            )
            for stage in stages
        ],
    )


# ============================================================
# GET SKIPPED STAGES
#
# GET /crop-stages/skipped?crop_season_id=...
# ============================================================


@router.get(
    "/skipped",
    response_model=ApiResponse[list[CropStageResponse]],
)
def get_skipped_crop_stages_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    _verify_crop_access(
        crop,
        farmer,
    )

    repository = CropStageRepository(db)

    stages = get_skipped_stages(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Skipped crop stages retrieved successfully.",
        data=[
            CropStageResponse.model_validate(
                stage,
            )
            for stage in stages
        ],
    )


# ============================================================
# COMPLETION STATUS
#
# GET /crop-stages/completion-status?crop_season_id=...
#
# COMPLETED + SKIPPED = FINISHED
# ============================================================


@router.get(
    "/completion-status",
    response_model=ApiResponse[dict[str, bool]],
)
def crop_stage_completion_status_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    _verify_crop_access(
        crop,
        farmer,
    )

    repository = CropStageRepository(db)

    all_finished = all_stages_completed(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message=(
            "Crop stage completion status "
            "retrieved successfully."
        ),
        data={
            "all_stages_finished": all_finished,
        },
    )


# ============================================================
# GET NEXT STAGE
#
# GET /crop-stages/{stage_id}/next
#
# Does NOT activate the stage.
# ============================================================


@router.get(
    "/{stage_id}/next",
    response_model=ApiResponse[CropStageResponse | None],
)
def get_next_stage_endpoint(
    stage_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    repository = CropStageRepository(db)

    next_stage = get_next_stage(
        repository=repository,
        stage=stage,
    )

    return ApiResponse(
        success=True,
        message="Next crop stage retrieved successfully.",
        data=(
            CropStageResponse.model_validate(
                next_stage,
            )
            if next_stage is not None
            else None
        ),
    )


# ============================================================
# ACTIVATE STAGE
#
# PATCH /crop-stages/{stage_id}/activate
#
# PENDING → ACTIVE
# ============================================================


@router.patch(
    "/{stage_id}/activate",
    response_model=ApiResponse[CropStageResponse],
)
def activate_crop_stage_endpoint(
    stage_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    repository = CropStageRepository(db)

    stage = activate_stage(
        repository=repository,
        stage=stage,
    )

    return ApiResponse(
        success=True,
        message="Crop stage activated successfully.",
        data=CropStageResponse.model_validate(
            stage,
        ),
    )


# ============================================================
# COMPLETE STAGE
#
# PATCH /crop-stages/{stage_id}/complete
#
# ACTIVE → COMPLETED
#
# NEXT PENDING → ACTIVE
# ============================================================


@router.patch(
    "/{stage_id}/complete",
    response_model=ApiResponse[CropStageResponse],
)
def complete_crop_stage_endpoint(
    stage_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    repository = CropStageRepository(db)

    stage = complete_stage(
        repository=repository,
        stage=stage,
    )

    return ApiResponse(
        success=True,
        message="Crop stage completed successfully.",
        data=CropStageResponse.model_validate(
            stage,
        ),
    )


# ============================================================
# SKIP STAGE
#
# PATCH /crop-stages/{stage_id}/skip
#
# ACTIVE → SKIPPED
#
# NEXT PENDING → ACTIVE
# ============================================================


@router.patch(
    "/{stage_id}/skip",
    response_model=ApiResponse[CropStageResponse],
)
def skip_crop_stage_endpoint(
    stage_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    repository = CropStageRepository(db)

    stage = skip_stage(
        repository=repository,
        stage=stage,
    )

    return ApiResponse(
        success=True,
        message="Crop stage skipped successfully.",
        data=CropStageResponse.model_validate(
            stage,
        ),
    )


# ============================================================
# UPDATE STAGE
#
# PUT /crop-stages/{stage_id}
#
# CropSeason = PLANNED
# Stage      = PENDING
#
# Status CANNOT be changed here.
# ============================================================


@router.put(
    "/{stage_id}",
    response_model=ApiResponse[CropStageResponse],
)
def update_crop_stage_endpoint(
    stage_id: UUID,
    request: CropStageUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    repository = CropStageRepository(db)

    stage = update_stage(
        repository=repository,
        stage=stage,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Crop stage updated successfully.",
        data=CropStageResponse.model_validate(
            stage,
        ),
    )


# ============================================================
# DELETE STAGE
#
# DELETE /crop-stages/{stage_id}
#
# CropSeason = PLANNED
# Stage      = PENDING
# Last stage only
# ============================================================


@router.delete(
    "/{stage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_crop_stage_endpoint(
    stage_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    repository = CropStageRepository(db)

    delete_stage(
        repository=repository,
        stage=stage,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# ============================================================
# GET STAGE BY ID
#
# GET /crop-stages/{stage_id}
#
# IMPORTANT:
#
# Generic route remains LAST.
# ============================================================


@router.get(
    "/{stage_id}",
    response_model=ApiResponse[CropStageResponse],
)
def get_crop_stage_endpoint(
    stage_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    return ApiResponse(
        success=True,
        message="Crop stage retrieved successfully.",
        data=CropStageResponse.model_validate(
            stage,
        ),
    )