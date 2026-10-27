from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_farmer
from app.database.session import get_db

from app.modules.activity.repository import ActivityRepository
from app.modules.advisor.service import AdvisorService
from app.modules.chat.session_repository import SessionRepository
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.crop_stage.repository import CropStageRepository
from app.modules.dashboard.schemas import DashboardResponse
from app.modules.dashboard.service import DashboardService
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.models import Farmer
from app.modules.weather.service import WeatherService

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=ApiResponse[DashboardResponse],
)
async def get_dashboard(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
) -> ApiResponse[DashboardResponse]:

    # ============================================================
    # REPOSITORIES
    # ============================================================

    farm_repository = FarmRepository(db)

    crop_repository = CropSeasonRepository(db)

    # NEW: Crop Stage Repository
    crop_stage_repository = CropStageRepository(db)

    activity_repository = ActivityRepository(db)

    session_repository = SessionRepository(db)

    # ============================================================
    # SERVICES
    # ============================================================

    weather_service = WeatherService()

    advisor_service = AdvisorService(
        farm_repository=farm_repository,
        crop_repository=crop_repository,
        activity_repository=activity_repository,
    )

    # ============================================================
    # DASHBOARD SERVICE
    # ============================================================

    dashboard_service = DashboardService(
        farm_repository=farm_repository,
        crop_repository=crop_repository,

        # NEW: required by DashboardService
        crop_stage_repository=crop_stage_repository,

        activity_repository=activity_repository,
        session_repository=session_repository,
        weather_service=weather_service,
        advisor_service=advisor_service,
    )

    # ============================================================
    # GET DASHBOARD DATA
    # ============================================================

    dashboard_data = await dashboard_service.get_dashboard(
        current_farmer,
    )

    # ============================================================
    # API RESPONSE
    # ============================================================

    return ApiResponse(
        success=True,
        message="Dashboard loaded successfully.",
        data=dashboard_data,
    )