from datetime import date
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

from app.modules.farmer.repository import (
    FarmerRepository,
)

from app.modules.crop_season.models import (
    CropSeasonStatus,
)

from app.modules.crop_season.repository import (
    CropSeasonRepository,
)

from app.modules.crop_stage.repository import (
    CropStageRepository,
)

from app.modules.activity.models import (
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
)

from app.modules.activity.repository import (
    ActivityRepository,
)

from app.modules.activity.schemas import (
    ActivityCreateRequest,
    ActivityResponse,
    ActivityUpdateRequest,
)

from app.modules.activity.service import (
    complete_activity,
    create_activity,
    delete_activity,
    get_activities_by_date_range,
    get_activities_by_priority,
    get_activities_by_source,
    get_activities_by_status,
    get_activity,
    get_completed_activities,
    get_crop_activities,
    get_in_progress_activities,
    get_overdue_activities,
    get_pending_activities,
    get_skipped_activities,
    get_stage_activities,
    get_today_activities,
    get_today_completed_activities,
    get_today_in_progress_activities,
    get_today_pending_activities,
    get_today_incomplete_activities,
    get_upcoming_activities,
    skip_activity,
    start_activity,
    update_activity,
)

from app.shared.exceptions import (
    ActivityNotFoundError,
)

from app.shared.responses import (
    ApiResponse,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/activities",
    tags=["Activity"],
)


# ============================================================
# PRIVATE HELPERS
# ============================================================


def _get_farmer(
    db: Session,
    current_user: User,
):
    """
    Get farmer profile belonging to the authenticated user.
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


# ============================================================
# GET CROP SEASON
# ============================================================


def _get_crop_season(
    db: Session,
    crop_season_id: UUID,
):
    """
    Get crop season by ID.
    """

    repository = CropSeasonRepository(db)

    crop = repository.get_by_id(
        crop_season_id,
    )

    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop season not found.",
        )

    return crop


# ============================================================
# GET CROP STATUS
# ============================================================


def _get_crop_status(
    crop,
):
    """
    Normalize CropSeason status.

    Supports:

        CropSeasonStatus.ACTIVE

    and:

        "ACTIVE"
    """

    crop_status = crop.status

    if hasattr(
        crop_status,
        "value",
    ):
        return crop_status.value

    return crop_status


# ============================================================
# VERIFY CROP ACCESS
# ============================================================


def _verify_crop_access(
    crop,
    farmer,
) -> None:
    """
    Verify ownership:

        CropSeason
            ↓
        Farm
            ↓
        Farmer
    """

    if crop.farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found.",
        )

    if crop.farm.farmer_id != farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


# ============================================================
# GET ACTIVITY
# ============================================================


def _get_activity(
    db: Session,
    activity_id: UUID,
):
    """
    Get activity by ID.

    Convert service-level ActivityNotFoundError
    into HTTP 404.
    """

    repository = ActivityRepository(db)

    try:
        return get_activity(
            repository=repository,
            activity_id=activity_id,
        )

    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found.",
        )


# ============================================================
# VERIFY ACTIVITY ACCESS
# ============================================================


def _verify_activity_access(
    activity,
    farmer,
) -> None:
    """
    Verify ownership:

        Activity
            ↓
        CropSeason
            ↓
        Farm
            ↓
        Farmer
    """

    if activity.crop_season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop season not found.",
        )

    if activity.crop_season.farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found.",
        )

    if (
        activity.crop_season.farm.farmer_id
        != farmer.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


# ============================================================
# GET STAGE
# ============================================================


def _get_stage(
    db: Session,
    stage_id: UUID,
):
    """
    Get crop stage by ID.
    """

    repository = CropStageRepository(db)

    stage = repository.get_by_id(
        stage_id,
    )

    if stage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop stage not found.",
        )

    return stage


# ============================================================
# VERIFY STAGE ACCESS
# ============================================================


def _verify_stage_access(
    stage,
    farmer,
) -> None:
    """
    Verify ownership:

        CropStage
            ↓
        CropSeason
            ↓
        Farm
            ↓
        Farmer
    """

    if stage.crop_season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop season not found.",
        )

    if stage.crop_season.farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found.",
        )

    if (
        stage.crop_season.farm.farmer_id
        != farmer.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


# ============================================================
# VERIFY STAGE BELONGS TO CROP
# ============================================================


def _verify_stage_belongs_to_crop(
    db: Session,
    stage_id: UUID,
    crop_season_id: UUID,
    farmer,
) -> None:
    """
    Verify:

    1. Stage exists.
    2. Stage belongs to authenticated farmer.
    3. Stage belongs to requested crop season.
    """

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    if stage.crop_season_id != crop_season_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected crop stage does not belong "
                "to this crop season."
            ),
        )


# ============================================================
# REQUIRE ACTIVE CROP
# ============================================================


def _require_active_crop(
    crop,
) -> None:
    """
    Operations that change farming progress require
    an ACTIVE crop season.

    Used for:

        START
        COMPLETE
        SKIP
    """

    crop_status = _get_crop_status(
        crop,
    )

    active_status = CropSeasonStatus.ACTIVE

    if hasattr(
        active_status,
        "value",
    ):
        active_status = active_status.value

    if crop_status != active_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Crop farming must be active before "
                "performing this activity operation."
            ),
        )


# ============================================================
# REQUIRE CROP NOT FINISHED
# ============================================================


def _require_crop_not_finished(
    crop,
) -> None:
    """
    Prevent modification of activities after
    the crop season has ended.

    Final states:

        HARVESTED
        CANCELLED
    """

    crop_status = _get_crop_status(
        crop,
    )

    harvested_status = CropSeasonStatus.HARVESTED
    cancelled_status = CropSeasonStatus.CANCELLED

    if hasattr(
        harvested_status,
        "value",
    ):
        harvested_status = harvested_status.value

    if hasattr(
        cancelled_status,
        "value",
    ):
        cancelled_status = cancelled_status.value

    if crop_status in (
        harvested_status,
        cancelled_status,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Activities cannot be modified after "
                "the crop season has ended."
            ),
        )


# ============================================================
# REQUIRE CROP CAN ADD ACTIVITY
# ============================================================


def _require_crop_can_add_activity(
    crop,
) -> None:
    """
    Activities can be added while the crop is:

        PLANNED
        ACTIVE

    Activities cannot be added after:

        HARVESTED
        CANCELLED
    """

    crop_status = _get_crop_status(
        crop,
    )

    harvested_status = CropSeasonStatus.HARVESTED
    cancelled_status = CropSeasonStatus.CANCELLED

    if hasattr(
        harvested_status,
        "value",
    ):
        harvested_status = harvested_status.value

    if hasattr(
        cancelled_status,
        "value",
    ):
        cancelled_status = cancelled_status.value

    if crop_status in (
        harvested_status,
        cancelled_status,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Activities cannot be added to a "
                "harvested or cancelled crop season."
            ),
        )


# ============================================================
# REQUIRE CROP CAN DELETE ACTIVITY
# ============================================================


def _require_crop_can_delete_activity(
    crop,
) -> None:
    """
    Activities cannot be deleted after the crop
    season has ended.
    """

    crop_status = _get_crop_status(
        crop,
    )

    harvested_status = CropSeasonStatus.HARVESTED
    cancelled_status = CropSeasonStatus.CANCELLED

    if hasattr(
        harvested_status,
        "value",
    ):
        harvested_status = harvested_status.value

    if hasattr(
        cancelled_status,
        "value",
    ):
        cancelled_status = cancelled_status.value

    if crop_status in (
        harvested_status,
        cancelled_status,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Activities cannot be deleted after "
                "the crop season has ended."
            ),
        )


# ============================================================
# VALIDATE DATE RANGE
# ============================================================


def _validate_date_range(
    start_date: date,
    end_date: date,
) -> None:
    """
    Validate date range.
    """

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "End date must be greater than or equal "
                "to start date."
            ),
        )


# ============================================================
# CREATE ACTIVITY
#
# POST /activities?crop_season_id={uuid}
#
# Allowed crop states:
#
#     PLANNED
#     ACTIVE
# ============================================================


@router.post(
    "",
    response_model=ApiResponse[ActivityResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_activity_endpoint(
    crop_season_id: UUID,
    request: ActivityCreateRequest,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    _require_crop_can_add_activity(
        crop,
    )

    # --------------------------------------------------------
    # Verify optional stage.
    # --------------------------------------------------------

    if request.stage_id is not None:
        _verify_stage_belongs_to_crop(
            db=db,
            stage_id=request.stage_id,
            crop_season_id=crop.id,
            farmer=farmer,
        )

    repository = ActivityRepository(db)

    activity = create_activity(
        repository=repository,
        crop_season_id=crop.id,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Activity created successfully.",
        data=ActivityResponse.model_validate(
            activity,
        ),
    )


# ============================================================
# LIST ALL ACTIVITIES
#
# GET /activities?crop_season_id={uuid}
# ============================================================


@router.get(
    "",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def list_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_crop_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# TODAY
#
# GET /activities/today?crop_season_id={uuid}
# ============================================================


@router.get(
    "/today",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def today_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_today_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Today's activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# TODAY INCOMPLETE
#
# GET /activities/today/incomplete
#
# PENDING + IN_PROGRESS
# ============================================================


@router.get(
    "/today/incomplete",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def today_incomplete_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_today_incomplete_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message=(
            "Today's incomplete activities "
            "retrieved successfully."
        ),
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# TODAY PENDING
#
# GET /activities/today/pending
# ============================================================


@router.get(
    "/today/pending",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def today_pending_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_today_pending_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message=(
            "Today's pending activities "
            "retrieved successfully."
        ),
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# TODAY IN-PROGRESS
#
# GET /activities/today/in-progress
# ============================================================


@router.get(
    "/today/in-progress",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def today_in_progress_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_today_in_progress_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message=(
            "Today's in-progress activities "
            "retrieved successfully."
        ),
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# TODAY COMPLETED
#
# GET /activities/today/completed
# ============================================================


@router.get(
    "/today/completed",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def today_completed_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_today_completed_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message=(
            "Today's completed activities "
            "retrieved successfully."
        ),
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# PENDING
#
# GET /activities/pending
# ============================================================


@router.get(
    "/pending",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def pending_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_pending_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Pending activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# IN-PROGRESS
#
# GET /activities/in-progress
# ============================================================


@router.get(
    "/in-progress",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def in_progress_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_in_progress_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message=(
            "In-progress activities "
            "retrieved successfully."
        ),
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# COMPLETED
#
# GET /activities/completed
# ============================================================


@router.get(
    "/completed",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def completed_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_completed_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Completed activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# SKIPPED
#
# GET /activities/skipped
# ============================================================


@router.get(
    "/skipped",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def skipped_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_skipped_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Skipped activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# UPCOMING
#
# GET /activities/upcoming
#
# PENDING + IN_PROGRESS
# scheduled_date >= today
# ============================================================


@router.get(
    "/upcoming",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def upcoming_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_upcoming_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Upcoming activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# OVERDUE
#
# GET /activities/overdue
#
# scheduled_date < today
#
# PENDING + IN_PROGRESS
# ============================================================


@router.get(
    "/overdue",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def overdue_activities_endpoint(
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_overdue_activities(
        repository=repository,
        crop_season_id=crop.id,
    )

    return ApiResponse(
        success=True,
        message="Overdue activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# BY STATUS
#
# GET /activities/status/{activity_status}
# ============================================================


@router.get(
    "/status/{activity_status}",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def activities_by_status_endpoint(
    activity_status: ActivityStatus,
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_activities_by_status(
        repository=repository,
        crop_season_id=crop.id,
        activity_status=activity_status,
    )

    return ApiResponse(
        success=True,
        message="Activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# BY SOURCE
#
# GET /activities/source/{source}
# ============================================================


@router.get(
    "/source/{source}",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def activities_by_source_endpoint(
    source: ActivitySource,
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_activities_by_source(
        repository=repository,
        crop_season_id=crop.id,
        source=source,
    )

    return ApiResponse(
        success=True,
        message="Activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# BY PRIORITY
#
# GET /activities/priority/{priority}
# ============================================================


@router.get(
    "/priority/{priority}",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def activities_by_priority_endpoint(
    priority: ActivityPriority,
    crop_season_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    repository = ActivityRepository(db)

    activities = get_activities_by_priority(
        repository=repository,
        crop_season_id=crop.id,
        priority=priority,
    )

    return ApiResponse(
        success=True,
        message="Activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# DATE RANGE
#
# GET /activities/date-range
#
# Example:
#
# /activities/date-range
#     ?crop_season_id=UUID
#     &start_date=2026-08-01
#     &end_date=2026-08-15
# ============================================================


@router.get(
    "/date-range",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def activities_by_date_range_endpoint(
    crop_season_id: UUID,
    start_date: date,
    end_date: date,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
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

    _validate_date_range(
        start_date,
        end_date,
    )

    repository = ActivityRepository(db)

    activities = get_activities_by_date_range(
        repository=repository,
        crop_season_id=crop.id,
        start_date=start_date,
        end_date=end_date,
    )

    return ApiResponse(
        success=True,
        message="Activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# BY STAGE
#
# GET /activities/stage/{stage_id}
# ============================================================


@router.get(
    "/stage/{stage_id}",
    response_model=ApiResponse[
        list[ActivityResponse]
    ],
)
def get_stage_activities_endpoint(
    stage_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    stage = _get_stage(
        db,
        stage_id,
    )

    _verify_stage_access(
        stage,
        farmer,
    )

    repository = ActivityRepository(db)

    activities = get_stage_activities(
        repository=repository,
        stage_id=stage.id,
    )

    return ApiResponse(
        success=True,
        message="Stage activities retrieved successfully.",
        data=[
            ActivityResponse.model_validate(
                activity,
            )
            for activity in activities
        ],
    )


# ============================================================
# GET ACTIVITY BY ID
#
# IMPORTANT:
#
# This generic route must remain after all static GET routes.
#
# GET /activities/{activity_id}
# ============================================================


@router.get(
    "/{activity_id}",
    response_model=ApiResponse[ActivityResponse],
)
def get_activity_endpoint(
    activity_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    activity = _get_activity(
        db,
        activity_id,
    )

    _verify_activity_access(
        activity,
        farmer,
    )

    return ApiResponse(
        success=True,
        message="Activity retrieved successfully.",
        data=ActivityResponse.model_validate(
            activity,
        ),
    )


# ============================================================
# UPDATE ACTIVITY
#
# PUT /activities/{activity_id}
#
# Only PENDING activities can be edited.
#
# stage_id can be:
#
#     UUID -> attach stage
#     null -> remove stage
# ============================================================


@router.put(
    "/{activity_id}",
    response_model=ApiResponse[ActivityResponse],
)
def update_activity_endpoint(
    activity_id: UUID,
    request: ActivityUpdateRequest,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    activity = _get_activity(
        db,
        activity_id,
    )

    _verify_activity_access(
        activity,
        farmer,
    )

    # --------------------------------------------------------
    # Crop cannot be harvested/cancelled.
    # --------------------------------------------------------

    _require_crop_not_finished(
        activity.crop_season,
    )

    # --------------------------------------------------------
    # If stage_id is supplied as a UUID, verify ownership.
    #
    # If stage_id is null, the farmer is intentionally
    # removing the existing stage, so no stage lookup
    # is required.
    # --------------------------------------------------------

    if request.stage_id is not None:

        _verify_stage_belongs_to_crop(
            db=db,
            stage_id=request.stage_id,
            crop_season_id=activity.crop_season_id,
            farmer=farmer,
        )

    repository = ActivityRepository(db)

    activity = update_activity(
        repository=repository,
        activity=activity,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Activity updated successfully.",
        data=ActivityResponse.model_validate(
            activity,
        ),
    )


# ============================================================
# START ACTIVITY
#
# PATCH /activities/{activity_id}/start
#
# PENDING
#     ↓
# IN_PROGRESS
# ============================================================


@router.patch(
    "/{activity_id}/start",
    response_model=ApiResponse[ActivityResponse],
)
def start_activity_endpoint(
    activity_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    activity = _get_activity(
        db,
        activity_id,
    )

    _verify_activity_access(
        activity,
        farmer,
    )

    # --------------------------------------------------------
    # Progress-changing operation requires ACTIVE crop.
    # --------------------------------------------------------

    _require_active_crop(
        activity.crop_season,
    )

    repository = ActivityRepository(db)

    activity = start_activity(
        repository=repository,
        activity=activity,
    )

    return ApiResponse(
        success=True,
        message="Activity started successfully.",
        data=ActivityResponse.model_validate(
            activity,
        ),
    )


# ============================================================
# COMPLETE ACTIVITY
#
# PATCH /activities/{activity_id}/complete
#
# IN_PROGRESS
#       ↓
# COMPLETED
# ============================================================


@router.patch(
    "/{activity_id}/complete",
    response_model=ApiResponse[ActivityResponse],
)
def complete_activity_endpoint(
    activity_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    activity = _get_activity(
        db,
        activity_id,
    )

    _verify_activity_access(
        activity,
        farmer,
    )

    _require_active_crop(
        activity.crop_season,
    )

    repository = ActivityRepository(db)

    activity = complete_activity(
        repository=repository,
        activity=activity,
    )

    return ApiResponse(
        success=True,
        message="Activity completed successfully.",
        data=ActivityResponse.model_validate(
            activity,
        ),
    )


# ============================================================
# SKIP ACTIVITY
#
# PATCH /activities/{activity_id}/skip
#
# PENDING / IN_PROGRESS
#          ↓
#       SKIPPED
# ============================================================


@router.patch(
    "/{activity_id}/skip",
    response_model=ApiResponse[ActivityResponse],
)
def skip_activity_endpoint(
    activity_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    activity = _get_activity(
        db,
        activity_id,
    )

    _verify_activity_access(
        activity,
        farmer,
    )

    _require_active_crop(
        activity.crop_season,
    )

    repository = ActivityRepository(db)

    activity = skip_activity(
        repository=repository,
        activity=activity,
    )

    return ApiResponse(
        success=True,
        message="Activity skipped successfully.",
        data=ActivityResponse.model_validate(
            activity,
        ),
    )


# ============================================================
# DELETE ACTIVITY
#
# DELETE /activities/{activity_id}
#
# Allowed:
#
#     PENDING
#     IN_PROGRESS
#
# Not allowed:
#
#     COMPLETED
#     SKIPPED
# ============================================================


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_activity_endpoint(
    activity_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_farmer(
        db,
        current_user,
    )

    activity = _get_activity(
        db,
        activity_id,
    )

    _verify_activity_access(
        activity,
        farmer,
    )

    _require_crop_can_delete_activity(
        activity.crop_season,
    )

    repository = ActivityRepository(db)

    delete_activity(
        repository=repository,
        activity=activity,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )