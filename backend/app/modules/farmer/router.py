from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db
from app.modules.identity.models import User

from app.modules.farmer.repository import FarmerRepository
from app.modules.farmer.schemas import (
    FarmerCreateRequest,
    FarmerUpdateRequest,
    FarmerResponse,
)
from app.modules.farmer.service import (
    create_farmer_profile,
    get_farmer_profile,
    update_farmer_profile,
)
from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/farmer",
    tags=["Farmer"],
)


# ============================================================
# CREATE FARMER PROFILE
# ============================================================


@router.post(
    "/profile",
    response_model=ApiResponse[FarmerResponse],
    status_code=201,
)
def create_profile(
    request: FarmerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = FarmerRepository(db)

    farmer = create_farmer_profile(
        repository=repository,
        user_id=current_user.id,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Farmer profile created successfully.",
        data=FarmerResponse.model_validate(farmer),
    )


# ============================================================
# GET FARMER PROFILE
# ============================================================


@router.get(
    "/profile",
    response_model=ApiResponse[FarmerResponse],
)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = FarmerRepository(db)

    farmer = get_farmer_profile(
        repository=repository,
        user_id=current_user.id,
    )

    return ApiResponse(
        success=True,
        message="Farmer profile retrieved successfully.",
        data=FarmerResponse.model_validate(farmer),
    )


# ============================================================
# UPDATE FARMER PROFILE
# ============================================================


@router.patch(
    "/profile",
    response_model=ApiResponse[FarmerResponse],
)
def update_profile(
    request: FarmerUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = FarmerRepository(db)

    farmer = update_farmer_profile(
        repository=repository,
        user_id=current_user.id,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Farmer profile updated successfully.",
        data=FarmerResponse.model_validate(farmer),
    )