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

from app.modules.farmer.repository import FarmerRepository
from app.modules.farm.repository import FarmRepository
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.activity.repository import ActivityRepository

from app.modules.chat.session_repository import SessionRepository
from app.modules.chat.message_repository import MessageRepository
from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
)
from app.modules.chat.service import ChatService

from app.modules.weather.service import WeatherService

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/ask-fm",
    tags=["🌱 Ask FM"],
)


@router.post(
    "",
    response_model=ApiResponse[ChatResponse],
)
async def ask_fm(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = FarmerRepository(db).get_by_user_id(
        current_user.id,
    )

    if farmer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found.",
        )

    service = ChatService(
        farm_repository=FarmRepository(db),
        crop_repository=CropSeasonRepository(db),
        activity_repository=ActivityRepository(db),
        session_repository=SessionRepository(db),
        message_repository=MessageRepository(db),
        weather_service=WeatherService(),
    )

    answer = await service.chat(
        current_farmer=farmer,
        message=request.message,
    )

    return ApiResponse(
        success=True,
        message="AI response generated successfully.",
        data=ChatResponse(
            answer=answer,
        ),
    )