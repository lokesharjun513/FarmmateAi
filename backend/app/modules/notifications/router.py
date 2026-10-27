from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.auth import (
    get_current_user,
)
from app.database.session import (
    get_db,
)
from app.modules.farmer.repository import (
    FarmerRepository,
)
from app.modules.identity.models import (
    User,
)
from app.modules.notifications.repository import (
    NotificationRepository,
)
from app.modules.notifications.repository_device import (
    DeviceTokenRepository,
)
from app.modules.notifications.schemas import (
    DeviceTokenRegisterRequest,
    NotificationCreateRequest,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.modules.notifications.service import (
    create_notification,
    delete_notification,
    get_notification,
    get_unread_notification_count,
    list_notifications,
    list_unread_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.modules.notifications.service_device import (
    deactivate_device_token,
    register_device_token,
)
from app.shared.exceptions import (
    NotificationNotFoundError,
)
from app.shared.responses import (
    ApiResponse,
)

# ============================================================
# ROUTER
# ============================================================


router = APIRouter(
    prefix="/notifications",
    tags=["Notification"],
)


# ============================================================
# PRIVATE HELPERS
# ============================================================


def _get_current_farmer(
    db: Session,
    current_user: User,
):
    """
    Get the farmer profile belonging to the
    authenticated user.
    """

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

    return farmer


def _get_notification_or_404(
    repository: NotificationRepository,
    notification_id: UUID,
):
    """
    Get notification or convert the domain exception
    into an HTTP 404 response.
    """

    try:
        return get_notification(
            repository=repository,
            notification_id=notification_id,
        )

    except NotificationNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )


def _verify_notification_access(
    notification: object,
    farmer: object,
) -> None:
    """
    Ensure the notification belongs to the
    authenticated farmer.
    """

    if notification.farmer_id != farmer.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )


# ============================================================
# CREATE NOTIFICATION
#
# POST /api/v1/notifications
#
# The farmer is determined from the authenticated user.
#
# farmer_id is NEVER accepted from the request body.
# ============================================================


@router.post(
    "",
    response_model=ApiResponse[NotificationResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_notification_endpoint(
    request: NotificationCreateRequest,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )
    device_repository = DeviceTokenRepository(
        db,
    )

    notification = create_notification(
        repository=repository,
        device_repository=device_repository,
        farmer_id=farmer.id,
        request=request,
    )

    return ApiResponse(
        success=True,
        message="Notification created successfully.",
        data=NotificationResponse.model_validate(
            notification,
        ),
    )


# ============================================================
# LIST ALL NOTIFICATIONS
#
# GET /api/v1/notifications
# ============================================================


@router.get(
    "",
    response_model=ApiResponse[
        list[NotificationResponse]
    ],
)
def list_notifications_endpoint(
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )

    notifications = list_notifications(
        repository=repository,
        farmer_id=farmer.id,
    )

    return ApiResponse(
        success=True,
        message="Notifications retrieved successfully.",
        data=[
            NotificationResponse.model_validate(
                notification,
            )
            for notification in notifications
        ],
    )


# ============================================================
# LIST UNREAD NOTIFICATIONS
#
# GET /api/v1/notifications/unread
#
# IMPORTANT:
# This route must be registered before /{notification_id}.
# ============================================================


@router.get(
    "/unread",
    response_model=ApiResponse[
        list[NotificationResponse]
    ],
)
def unread_notifications_endpoint(
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )

    notifications = list_unread_notifications(
        repository=repository,
        farmer_id=farmer.id,
    )

    return ApiResponse(
        success=True,
        message="Unread notifications retrieved successfully.",
        data=[
            NotificationResponse.model_validate(
                notification,
            )
            for notification in notifications
        ],
    )


# ============================================================
# GET UNREAD COUNT
#
# GET /api/v1/notifications/unread-count
# ============================================================


@router.get(
    "/unread-count",
    response_model=ApiResponse[
        NotificationUnreadCountResponse
    ],
)
def unread_notification_count_endpoint(
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )

    unread_count = get_unread_notification_count(
        repository=repository,
        farmer_id=farmer.id,
    )

    return ApiResponse(
        success=True,
        message=(
            "Unread notification count "
            "retrieved successfully."
        ),
        data=NotificationUnreadCountResponse(
            unread_count=unread_count,
        ),
    )


# ============================================================
# MARK ALL AS READ
#
# PATCH /api/v1/notifications/read-all
#
# IMPORTANT:
# This route must be registered before /{notification_id}.
# ============================================================


@router.patch(
    "/read-all",
    response_model=ApiResponse[None],
)
def mark_all_read_endpoint(
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )

    mark_all_notifications_read(
        repository=repository,
        farmer_id=farmer.id,
    )

    return ApiResponse(
        success=True,
        message="All notifications marked as read.",
        data=None,
    )


# ============================================================
# GET NOTIFICATION BY ID
#
# GET /api/v1/notifications/{notification_id}
# ============================================================


@router.get(
    "/{notification_id}",
    response_model=ApiResponse[
        NotificationResponse
    ],
)
def get_notification_endpoint(
    notification_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )

    notification = _get_notification_or_404(
        repository,
        notification_id,
    )

    _verify_notification_access(
        notification,
        farmer,
    )

    return ApiResponse(
        success=True,
        message="Notification retrieved successfully.",
        data=NotificationResponse.model_validate(
            notification,
        ),
    )


# ============================================================
# MARK NOTIFICATION AS READ
#
# PATCH /api/v1/notifications/{notification_id}/read
#
# Idempotent:
#
# UNREAD → READ
# READ   → READ
# ============================================================


@router.patch(
    "/{notification_id}/read",
    response_model=ApiResponse[
        NotificationResponse
    ],
)
def mark_read_endpoint(
    notification_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )

    notification = _get_notification_or_404(
        repository,
        notification_id,
    )

    _verify_notification_access(
        notification,
        farmer,
    )

    notification = mark_notification_read(
        repository=repository,
        notification=notification,
    )

    return ApiResponse(
        success=True,
        message="Notification marked as read.",
        data=NotificationResponse.model_validate(
            notification,
        ),
    )


# ============================================================
# DELETE NOTIFICATION
#
# DELETE /api/v1/notifications/{notification_id}
# ============================================================


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification_endpoint(
    notification_id: UUID,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    repository = NotificationRepository(
        db,
    )

    notification = _get_notification_or_404(
        repository,
        notification_id,
    )

    _verify_notification_access(
        notification,
        farmer,
    )

    delete_notification(
        repository=repository,
        notification=notification,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# ============================================================
# REGISTER DEVICE TOKEN
#
# POST /api/v1/notifications/devices
# ============================================================


@router.post(
    "/devices",
    response_model=ApiResponse[None],
    status_code=status.HTTP_201_CREATED,
)
def register_device_endpoint(
    request: DeviceTokenRegisterRequest,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    register_device_token(
        db=db,
        farmer_id=farmer.id,
        fid=request.fid,
        device_name=request.device_name,
    )

    return ApiResponse(
        success=True,
        message="Device registration saved successfully.",
        data=None,
    )


# ============================================================
# DEACTIVATE DEVICE TOKEN
#
# DELETE /api/v1/notifications/devices/{fid}
# ============================================================


@router.delete(
    "/devices/{fid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_device_endpoint(
    fid: str,
    current_user: User = Depends(
        get_current_user,
    ),
    db: Session = Depends(
        get_db,
    ),
):

    farmer = _get_current_farmer(
        db,
        current_user,
    )

    deactivate_device_token(
        db=db,
        farmer_id=farmer.id,
        fid=fid,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
