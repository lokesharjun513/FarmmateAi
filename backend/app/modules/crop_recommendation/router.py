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

from app.modules.farm.repository import (
    FarmRepository,
)

from app.modules.crop_recommendation.schemas import (
    CropRecommendationRequest,
    CropRecommendationResponse,
)

from app.modules.crop_recommendation.service import (
    CropRecommendationService,
)

from app.modules.weather.service import (
    WeatherService,
)

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/crop-recommendation",
    tags=["Crop Recommendation"],
)


# ============================================================
# RECOMMEND CROPS
# ============================================================


@router.post(
    "",
    response_model=ApiResponse[
        CropRecommendationResponse
    ],
)
async def recommend_crop(
    request: CropRecommendationRequest,
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

    farmer_repository = FarmerRepository(
        db,
    )

    farmer = farmer_repository.get_by_user_id(
        current_user.id,
    )

    if farmer is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found.",
        )

    # --------------------------------------------------------
    # Get farm
    # --------------------------------------------------------

    farm_repository = FarmRepository(
        db,
    )

    farm = farm_repository.get_by_id(
        request.farm_id,
    )

    if farm is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found.",
        )

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------

    if farm.farmer_id != farmer.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this farm.",
        )

    # --------------------------------------------------------
    # Create service
    # --------------------------------------------------------

    service = CropRecommendationService(
        farm_repository=farm_repository,
        weather_service=WeatherService(),
    )

    # --------------------------------------------------------
    # Generate recommendation
    # --------------------------------------------------------

    recommendation = await service.recommend(
        farm_id=farm.id,
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return ApiResponse(
        success=True,
        message=(
            "Crop recommendations generated successfully."
        ),
        data=recommendation,
    )