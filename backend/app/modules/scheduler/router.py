from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User

from app.modules.activity.repository import ActivityRepository
from app.modules.chat.session_repository import SessionRepository
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.repository import FarmerRepository
from app.modules.notifications.repository import NotificationRepository

from app.modules.scheduler.schemas import (
    SchedulerRunResponse,
)
from app.modules.scheduler.service import (
    SchedulerService,
)

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler"],
)


@router.post(
    "/run",
    response_model=ApiResponse[SchedulerRunResponse],
)
async def run_scheduler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute all scheduled backend jobs.

    Future:
    - Restrict this endpoint to ADMIN users.
    - APScheduler/Cron can invoke the same service automatically.
    """

    service = SchedulerService(
        farm_repository=FarmRepository(db),
        farmer_repository=FarmerRepository(db),
        crop_repository=CropSeasonRepository(db),
        activity_repository=ActivityRepository(db),
        notification_repository=NotificationRepository(db),
        session_repository=SessionRepository(db),
    )

    result = await service.run()

    return ApiResponse(
        success=True,
        message="Scheduler executed successfully.",
        data=result,
    )