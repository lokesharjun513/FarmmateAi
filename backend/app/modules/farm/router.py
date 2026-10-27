from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User
from app.modules.farmer.repository import FarmerRepository
from app.modules.farm.repository import FarmRepository
from app.modules.farm.schemas import (
    FarmCreateRequest,
    FarmUpdateRequest,
    FarmResponse,
)
from app.modules.farm.service import (
    create_farm,
    get_farm,
    list_farms,
    update_farm,
    delete_farm,
)

from app.shared.exceptions import (
    FarmerProfileNotFoundError,
)

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/farms",
    tags=["Farm"],
)


# ============================================================
# CREATE FARM
# ============================================================


@router.post(
    "",
    response_model=ApiResponse[FarmResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_farm_endpoint(
    request: FarmCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer_repository = FarmerRepository(db)
    farm_repository = FarmRepository(db)

    farmer = farmer_repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    farm = create_farm(
        repository=farm_repository,
        farmer_id=farmer.id,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Farm created successfully.",
        data=FarmResponse.model_validate(farm),
    )


# ============================================================
# LIST FARMS
# ============================================================


@router.get(
    "",
    response_model=ApiResponse[list[FarmResponse]],
)
def get_all_farms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer_repository = FarmerRepository(db)
    farm_repository = FarmRepository(db)

    farmer = farmer_repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    farms = list_farms(
        repository=farm_repository,
        farmer_id=farmer.id,
    )

    return ApiResponse(
        success=True,
        message="Farms retrieved successfully.",
        data=[
            FarmResponse.model_validate(farm)
            for farm in farms
        ],
    )


# ============================================================
# GET FARM
# ============================================================


@router.get(
    "/{farm_id}",
    response_model=ApiResponse[FarmResponse],
)
def get_farm_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer_repository = FarmerRepository(db)
    farm_repository = FarmRepository(db)

    farmer = farmer_repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    farm = get_farm(
        repository=farm_repository,
        farm_id=farm_id,
        farmer_id=farmer.id,
    )

    return ApiResponse(
        success=True,
        message="Farm retrieved successfully.",
        data=FarmResponse.model_validate(farm),
    )


# ============================================================
# UPDATE FARM
# ============================================================


@router.patch(
    "/{farm_id}",
    response_model=ApiResponse[FarmResponse],
)
def update_farm_endpoint(
    farm_id: UUID,
    request: FarmUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer_repository = FarmerRepository(db)
    farm_repository = FarmRepository(db)

    farmer = farmer_repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    farm = get_farm(
        repository=farm_repository,
        farm_id=farm_id,
        farmer_id=farmer.id,
    )

    farm = update_farm(
        repository=farm_repository,
        farm=farm,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Farm updated successfully.",
        data=FarmResponse.model_validate(farm),
    )


# ============================================================
# DELETE FARM
# ============================================================


@router.delete(
    "/{farm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_farm_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer_repository = FarmerRepository(db)
    farm_repository = FarmRepository(db)

    farmer = farmer_repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    farm = get_farm(
        repository=farm_repository,
        farm_id=farm_id,
        farmer_id=farmer.id,
    )

    delete_farm(
        repository=farm_repository,
        farm=farm,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )