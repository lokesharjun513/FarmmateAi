from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_farmer
from app.database.session import get_db

from app.modules.activity.repository import ActivityRepository
from app.modules.advisor.schemas import DailyAdvisorResponse
from app.modules.advisor.service import AdvisorService
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.models import Farmer

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/advisor",
    tags=["AI Advisor"],
)


@router.get(
    "/today",
    response_model=ApiResponse[DailyAdvisorResponse],
)
async def get_today_advice(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):

    service = AdvisorService(
        farm_repository=FarmRepository(db),
        crop_repository=CropSeasonRepository(db),
        activity_repository=ActivityRepository(db),
    )

    advice = await service.get_today_advice(
        current_farmer=current_farmer,
    )

    return ApiResponse(
        success=True,
        message="Daily advisor generated successfully.",
        data=advice,
    )