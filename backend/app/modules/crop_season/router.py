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

from app.modules.farmer.repository import FarmerRepository
from app.modules.farm.repository import FarmRepository

from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.crop_season.schemas import (
    CropSeasonCancelRequest,
    CropSeasonCreateRequest,
    CropSeasonHarvestRequest,
    CropSeasonUpdateRequest,
    CropSeasonResponse,
)
from app.modules.crop_season.service import (
    create_crop_season,
    get_crop_season,
    get_crop_seasons,
    get_active_crop_season,
    get_active_crop_seasons,
    get_planned_crop_seasons,
    get_harvested_crop_seasons,
    get_cancelled_crop_seasons,
    get_latest_crop_season,
    update_crop_season,
    activate_crop_season,
    complete_crop_season,
    cancel_crop_season,
    delete_crop_season,
)

from app.modules.crop_stage.repository import CropStageRepository

from app.shared.exceptions import CropSeasonNotFoundError
from app.shared.responses import ApiResponse


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/crop-seasons",
    tags=["Crop Season"],
)


# ============================================================
# PRIVATE HELPERS
# ============================================================


def _get_farmer(
    db: Session,
    current_user: User,
):
    """
    Get the farmer profile belonging to the authenticated user.
    """

    repository = FarmerRepository(db)

    farmer = repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found.",
        )

    return farmer


def _get_farm(
    db: Session,
    farm_id: UUID,
):
    """
    Get a farm by ID.
    """

    repository = FarmRepository(db)

    farm = repository.get_by_id(
        farm_id,
    )

    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found.",
        )

    return farm


def _verify_farm_access(
    farm,
    farmer,
) -> None:
    """
    Verify that the farm belongs to the authenticated farmer.
    """

    if farm.farmer_id != farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


def _get_crop_season(
    db: Session,
    crop_season_id: UUID,
):
    """
    Get crop season by ID.

    Converts the service-level not-found exception
    into an HTTP 404 response.
    """

    repository = CropSeasonRepository(db)

    try:
        return get_crop_season(
            repository=repository,
            crop_season_id=crop_season_id,
        )

    except CropSeasonNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop season not found.",
        ) from exc


def _verify_crop_access(
    crop,
    farmer,
) -> None:
    """
    Verify that the crop season belongs to a farm
    owned by the authenticated farmer.
    """

    if crop.farm.farmer_id != farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


# ============================================================
# CREATE CROP SEASON
#
# POST /crop-seasons?farm_id=...
#
# New crop:
#
# PLANNED
# ============================================================


@router.post(
    "",
    response_model=ApiResponse[CropSeasonResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_crop_season_endpoint(
    farm_id: UUID,
    request: CropSeasonCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crop = create_crop_season(
        repository=repository,
        farm_id=farm.id,
        request=request,
        farm=farm,
    )

    return ApiResponse(
        success=True,
        message="Crop season created successfully.",
        data=CropSeasonResponse.model_validate(crop),
    )


# ============================================================
# LIST ALL CROP SEASONS
#
# GET /crop-seasons?farm_id=...
# ============================================================


@router.get(
    "",
    response_model=ApiResponse[list[CropSeasonResponse]],
)
def list_crop_seasons_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crops = get_crop_seasons(
        repository=repository,
        farm_id=farm.id,
    )

    return ApiResponse(
        success=True,
        message="Crop seasons retrieved successfully.",
        data=[
            CropSeasonResponse.model_validate(crop)
            for crop in crops
        ],
    )


# ============================================================
# GET ACTIVE CROP
#
# GET /crop-seasons/active?farm_id=...
# ============================================================


@router.get(
    "/active",
    response_model=ApiResponse[CropSeasonResponse | None],
)
def get_active_crop_season_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crop = get_active_crop_season(
        repository=repository,
        farm_id=farm.id,
    )

    return ApiResponse(
        success=True,
        message="Active crop season retrieved successfully.",
        data=(
            CropSeasonResponse.model_validate(crop)
            if crop is not None
            else None
        ),
    )


# ============================================================
# GET ALL ACTIVE CROP SEASONS
#
# GET /crop-seasons/active/all?farm_id=...
# ============================================================


@router.get(
    "/active/all",
    response_model=ApiResponse[list[CropSeasonResponse]],
)
def get_active_crop_seasons_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crops = get_active_crop_seasons(
        repository=repository,
        farm_id=farm.id,
    )

    return ApiResponse(
        success=True,
        message="Active crop seasons retrieved successfully.",
        data=[
            CropSeasonResponse.model_validate(crop)
            for crop in crops
        ],
    )


# ============================================================
# GET PLANNED CROP SEASONS
#
# GET /crop-seasons/planned?farm_id=...
# ============================================================


@router.get(
    "/planned",
    response_model=ApiResponse[list[CropSeasonResponse]],
)
def get_planned_crop_seasons_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crops = get_planned_crop_seasons(
        repository=repository,
        farm_id=farm.id,
    )

    return ApiResponse(
        success=True,
        message="Planned crop seasons retrieved successfully.",
        data=[
            CropSeasonResponse.model_validate(crop)
            for crop in crops
        ],
    )


# ============================================================
# GET HARVESTED CROP SEASONS
#
# GET /crop-seasons/harvested?farm_id=...
# ============================================================


@router.get(
    "/harvested",
    response_model=ApiResponse[list[CropSeasonResponse]],
)
def get_harvested_crop_seasons_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crops = get_harvested_crop_seasons(
        repository=repository,
        farm_id=farm.id,
    )

    return ApiResponse(
        success=True,
        message="Harvested crop seasons retrieved successfully.",
        data=[
            CropSeasonResponse.model_validate(crop)
            for crop in crops
        ],
    )


# ============================================================
# GET CANCELLED CROP SEASONS
#
# GET /crop-seasons/cancelled?farm_id=...
# ============================================================


@router.get(
    "/cancelled",
    response_model=ApiResponse[list[CropSeasonResponse]],
)
def get_cancelled_crop_seasons_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crops = get_cancelled_crop_seasons(
        repository=repository,
        farm_id=farm.id,
    )

    return ApiResponse(
        success=True,
        message="Cancelled crop seasons retrieved successfully.",
        data=[
            CropSeasonResponse.model_validate(crop)
            for crop in crops
        ],
    )


# ============================================================
# GET LATEST CROP SEASON
#
# GET /crop-seasons/latest?farm_id=...
# ============================================================


@router.get(
    "/latest",
    response_model=ApiResponse[CropSeasonResponse | None],
)
def get_latest_crop_season_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(
        db,
        current_user,
    )

    farm = _get_farm(
        db,
        farm_id,
    )

    _verify_farm_access(
        farm,
        farmer,
    )

    repository = CropSeasonRepository(db)

    crop = get_latest_crop_season(
        repository=repository,
        farm_id=farm.id,
    )

    return ApiResponse(
        success=True,
        message="Latest crop season retrieved successfully.",
        data=(
            CropSeasonResponse.model_validate(crop)
            if crop is not None
            else None
        ),
    )


# ============================================================
# GET CROP SEASON BY ID
#
# GET /crop-seasons/{crop_season_id}
#
# IMPORTANT:
# Static routes above this route must remain above it.
# ============================================================


@router.get(
    "/{crop_season_id}",
    response_model=ApiResponse[CropSeasonResponse],
)
def get_crop_season_endpoint(
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

    return ApiResponse(
        success=True,
        message="Crop season retrieved successfully.",
        data=CropSeasonResponse.model_validate(crop),
    )


# ============================================================
# UPDATE CROP SEASON
#
# PUT /crop-seasons/{crop_season_id}
#
# Only PLANNED crops can be edited.
# ============================================================


@router.put(
    "/{crop_season_id}",
    response_model=ApiResponse[CropSeasonResponse],
)
def update_crop_season_endpoint(
    crop_season_id: UUID,
    request: CropSeasonUpdateRequest,
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

    repository = CropSeasonRepository(db)

    stage_repository = CropStageRepository(db)

    crop = update_crop_season(
        repository=repository,
        crop_season=crop,
        request=request,
        stage_repository=stage_repository,
    )

    return ApiResponse(
        success=True,
        message="Crop season updated successfully.",
        data=CropSeasonResponse.model_validate(crop),
    )


# ============================================================
# START FARMING
#
# PATCH /crop-seasons/{crop_season_id}/start
#
# PLANNED
#     ↓
# ACTIVE
#
# First CropStage:
#
# PENDING
#     ↓
# ACTIVE
# ============================================================


@router.patch(
    "/{crop_season_id}/start",
    response_model=ApiResponse[CropSeasonResponse],
)
def start_crop_season_endpoint(
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

    crop_repository = CropSeasonRepository(db)

    stage_repository = CropStageRepository(db)

    crop = activate_crop_season(
        repository=crop_repository,
        stage_repository=stage_repository,
        crop_season=crop,
    )

    return ApiResponse(
        success=True,
        message="Farming started successfully.",
        data=CropSeasonResponse.model_validate(crop),
    )


# ============================================================
# COMPLETE / HARVEST CROP
#
# PATCH /crop-seasons/{crop_season_id}/complete
#
# ACTIVE
#     ↓
# HARVESTED
# ============================================================


@router.patch(
    "/{crop_season_id}/complete",
    response_model=ApiResponse[CropSeasonResponse],
)
def complete_crop_season_endpoint(
    crop_season_id: UUID,
    request: CropSeasonHarvestRequest | None = None,
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

    crop_repository = CropSeasonRepository(db)

    stage_repository = CropStageRepository(db)

    crop = complete_crop_season(
        repository=crop_repository,
        stage_repository=stage_repository,
        crop_season=crop,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Crop season harvested successfully.",
        data=CropSeasonResponse.model_validate(crop),
    )


# ============================================================
# CANCEL CROP SEASON
#
# PATCH /crop-seasons/{crop_season_id}/cancel
#
# PLANNED / ACTIVE
#     ↓
# CANCELLED
# ============================================================


@router.patch(
    "/{crop_season_id}/cancel",
    response_model=ApiResponse[CropSeasonResponse],
)
def cancel_crop_season_endpoint(
    crop_season_id: UUID,
    request: CropSeasonCancelRequest | None = None,
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

    repository = CropSeasonRepository(db)

    stage_repository = CropStageRepository(db)

    crop = cancel_crop_season(
        repository=repository,
        crop_season=crop,
        request=request,
        stage_repository=stage_repository,
    )

    return ApiResponse(
        success=True,
        message="Crop season cancelled successfully.",
        data=CropSeasonResponse.model_validate(crop),
    )


# ============================================================
# DELETE CROP SEASON
#
# DELETE /crop-seasons/{crop_season_id}
#
# Allowed:
#
# PLANNED
# CANCELLED
#
# Not allowed:
#
# ACTIVE
# HARVESTED
# ============================================================


@router.delete(
    "/{crop_season_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_crop_season_endpoint(
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

    repository = CropSeasonRepository(db)

    delete_crop_season(
        repository=repository,
        crop_season=crop,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )