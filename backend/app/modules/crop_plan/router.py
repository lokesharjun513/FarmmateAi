from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User

from app.modules.farmer.repository import (
    FarmerRepository,
)

from app.modules.crop_season.models import (
    CropSeasonStatus,
)

from app.modules.crop_season.repository import (
    CropSeasonRepository,
)

from app.modules.crop_plan.schemas import (
    CropPlanGenerateRequest,
    CropPlanRegenerateRequest,
    CropPlanResponse,
)

from app.modules.crop_plan.service import (
    generate_crop_plan,
    regenerate_crop_plan,
    get_crop_plan,
)

from app.modules.activity.repository import (
    ActivityRepository,
)

from app.shared.responses import (
    ApiResponse,
)


# ============================================================
# ROUTER
# ============================================================


router = APIRouter(
    prefix="/crop-plans",
    tags=["Crop Plan"],
)


# ============================================================
# PRIVATE HELPERS
# ============================================================


def _get_farmer(
    db: Session,
    current_user: User,
):
    """
    Get farmer profile belonging to the authenticated user.
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


# ============================================================
# GET CROP SEASON
# ============================================================


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


# ============================================================
# VERIFY CROP ACCESS
# ============================================================


def _verify_crop_access(
    crop,
    farmer,
) -> None:
    """
    Make sure the crop season belongs
    to the authenticated farmer.
    """

    if crop.farm is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found.",
        )

    if crop.farm.farmer_id != farmer.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


# ============================================================
# REQUIRE PLANNED CROP
# ============================================================


def _require_planned_crop(
    crop,
) -> None:
    """
    Crop plan generation and regeneration are only
    allowed while the crop season is PLANNED.
    """

    if crop.status != CropSeasonStatus.PLANNED:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Crop plan can only be generated or "
                "regenerated while the crop season is planned."
            ),
        )


# ============================================================
# GENERATE CROP PLAN
#
# POST /crop-plans/{crop_season_id}/generate
#
# PLANNED
#    ↓
# Generate stages
#    ↓
# Generate activities
# ============================================================


@router.post(
    "/{crop_season_id}/generate",
    response_model=ApiResponse[CropPlanResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_crop_plan_endpoint(
    crop_season_id: UUID,
    request: CropPlanGenerateRequest,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    # --------------------------------------------------------
    # Get farmer
    # --------------------------------------------------------

    farmer = _get_farmer(
        db,
        current_user,
    )

    # --------------------------------------------------------
    # Get crop season
    # --------------------------------------------------------

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------

    _verify_crop_access(
        crop,
        farmer,
    )

    # --------------------------------------------------------
    # Only PLANNED crop seasons can generate a plan.
    # --------------------------------------------------------

    _require_planned_crop(
        crop,
    )

    # --------------------------------------------------------
    # Repository
    # --------------------------------------------------------

    repository = ActivityRepository(
        db,
    )

    # --------------------------------------------------------
    # Generate plan
    # --------------------------------------------------------

    try:

        plan = generate_crop_plan(
            activity_repository=repository,
            crop_season_id=crop.id,
            request=request,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ApiResponse(
        success=True,
        message="Crop plan generated successfully.",
        data=plan,
    )


# ============================================================
# REGENERATE CROP PLAN
#
# POST /crop-plans/{crop_season_id}/regenerate
#
# Existing plan:
#
# stages
# activities
#
#      ↓
#
# DELETE
#      ↓
#
# CREATE NEW PLAN
#
# ============================================================


@router.post(
    "/{crop_season_id}/regenerate",
    response_model=ApiResponse[CropPlanResponse],
)
def regenerate_crop_plan_endpoint(
    crop_season_id: UUID,
    request: CropPlanRegenerateRequest,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    # --------------------------------------------------------
    # Get farmer
    # --------------------------------------------------------

    farmer = _get_farmer(
        db,
        current_user,
    )

    # --------------------------------------------------------
    # Get crop
    # --------------------------------------------------------

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------

    _verify_crop_access(
        crop,
        farmer,
    )

    # --------------------------------------------------------
    # Only PLANNED crops can regenerate.
    # --------------------------------------------------------

    _require_planned_crop(
        crop,
    )

    # --------------------------------------------------------
    # Repository
    # --------------------------------------------------------

    repository = ActivityRepository(
        db,
    )

    # --------------------------------------------------------
    # Regenerate
    # --------------------------------------------------------

    try:

        plan = regenerate_crop_plan(
            activity_repository=repository,
            crop_season_id=crop.id,
            request=request,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ApiResponse(
        success=True,
        message="Crop plan regenerated successfully.",
        data=plan,
    )


# ============================================================
# GET CROP PLAN
#
# GET /crop-plans/{crop_season_id}
#
# Returns:
#
# Crop Season
#     ↓
# Stages
#     ↓
# Activities
# ============================================================


@router.get(
    "/{crop_season_id}",
    response_model=ApiResponse[CropPlanResponse],
)
def get_crop_plan_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    # --------------------------------------------------------
    # Get farmer
    # --------------------------------------------------------

    farmer = _get_farmer(
        db,
        current_user,
    )

    # --------------------------------------------------------
    # Get crop
    # --------------------------------------------------------

    crop = _get_crop_season(
        db,
        crop_season_id,
    )

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------

    _verify_crop_access(
        crop,
        farmer,
    )

    # --------------------------------------------------------
    # Repository
    # --------------------------------------------------------

    repository = ActivityRepository(
        db,
    )

    # --------------------------------------------------------
    # Get plan
    # --------------------------------------------------------

    try:

        plan = get_crop_plan(
            activity_repository=repository,
            crop_season_id=crop.id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return ApiResponse(
        success=True,
        message="Crop plan retrieved successfully.",
        data=plan,
    )