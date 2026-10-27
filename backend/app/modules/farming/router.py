from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db
from app.modules.farmer.repository import FarmerRepository
from app.modules.farming.schemas import (
    GenerateFarmingPlanRequest,
    GenerateFarmingPlanResponse,
    StartFarmingRequest,
    StartFarmingResponse,
)
from app.modules.farming.service import (
    FarmingService,
)
from app.modules.identity.models import User
from app.shared.exceptions import (
    FarmerProfileNotFoundError,
)

router = APIRouter(
    prefix="/farming",
    tags=["Farming"],
)


def _get_current_farmer(
    current_user: User,
    db: Session,
):
    farmer = FarmerRepository(
        db,
    ).get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    return farmer


@router.post(
    "/plan",
    response_model=GenerateFarmingPlanResponse,
)
async def generate_farming_plan(
    request: GenerateFarmingPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_current_farmer(
        current_user=current_user,
        db=db,
    )

    service = FarmingService(
        db,
    )

    return await service.generate_plan(
        request=request,
        farmer_id=farmer.id,
    )


@router.post(
    "/start",
    response_model=StartFarmingResponse,
)
async def start_farming(
    request: StartFarmingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = _get_current_farmer(
        current_user=current_user,
        db=db,
    )

    service = FarmingService(
        db,
    )

    return await service.start_farming(
        request=request,
        farmer_id=farmer.id,
    )
