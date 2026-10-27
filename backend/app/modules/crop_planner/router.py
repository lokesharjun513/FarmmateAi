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

from app.modules.crop_season.repository import (
    CropSeasonRepository,
)

from app.modules.crop_planner.repository import (
    CropPlannerRepository,
)

from app.modules.crop_planner.schemas import (
    CropPlanGenerateRequest,
    CropPlanGenerateResponse,
)

from app.modules.crop_planner.service import (
    CropPlannerService,
)

from app.shared.responses import ApiResponse


router = APIRouter(
    prefix="/crop-planner",
    tags=["Crop Planner"],
)


# ============================================================
# GENERATE CROP PLAN
#
# POST
# /crop-planner/{crop_season_id}/generate
#
# Flow:
#
# CropSeason PLANNED
#       ↓
# AI generates plan
#       ↓
# Validate
#       ↓
# Create CropStages
#       ↓
# Create Activities
#       ↓
# Commit
#       ↓
# Return result
#
# ============================================================


@router.post(
    "/{crop_season_id}/generate",
    response_model=ApiResponse[
        CropPlanGenerateResponse
    ],
    status_code=status.HTTP_201_CREATED,
)
async def generate_crop_plan_endpoint(
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

    farmer_repo = FarmerRepository(
        db,
    )

    farmer = farmer_repo.get_by_user_id(
        current_user.id,
    )

    if farmer is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found.",
        )

    # --------------------------------------------------------
    # Get crop season
    # --------------------------------------------------------

    crop_repo = CropSeasonRepository(
        db,
    )

    crop_season = crop_repo.get_by_id(
        crop_season_id,
    )

    if crop_season is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop season not found.",
        )

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------

    if (
        crop_season.farm.farmer_id
        != farmer.id
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    # --------------------------------------------------------
    # Create planner repository
    # --------------------------------------------------------

    planner_repository = (
        CropPlannerRepository(
            db,
        )
    )

    # --------------------------------------------------------
    # Create planner service
    # --------------------------------------------------------

    service = CropPlannerService(
        repository=planner_repository,
    )

    # --------------------------------------------------------
    # Generate + save plan
    # --------------------------------------------------------

    plan = await service.generate_plan(
        crop_season=crop_season,

        state=request.state,

        district=request.district,

        village=request.village,

        soil_type=request.soil_type,
    )

    # --------------------------------------------------------
    # Count persisted stages and activities
    #
    # We know the exact generated counts from the plan.
    # --------------------------------------------------------

    stages_created = len(
        plan.stages,
    )

    activities_created = sum(
        len(stage.activities)
        for stage in plan.stages
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    result = CropPlanGenerateResponse(
        crop_season_id=crop_season.id,

        crop_name=plan.crop_name,

        crop_variety=plan.crop_variety,

        season=plan.season,

        estimated_duration_days=(
            plan.estimated_duration_days
        ),

        stages_created=stages_created,

        activities_created=activities_created,
    )

    return ApiResponse(
        success=True,

        message=(
            "Crop plan generated and saved "
            "successfully."
        ),

        data=result,
    )