import logging
from uuid import UUID

from app.modules.notifications.fcm_service import send_push_notification
from app.modules.notifications.models import (
    Notification,
)
from app.modules.notifications.repository import (
    NotificationRepository,
)
from app.modules.notifications.repository_device import (
    DeviceTokenRepository,
)
from app.modules.notifications.schemas import (
    NotificationCreateRequest,
)
from app.shared.exceptions import (
    NotificationNotFoundError,
)

logger = logging.getLogger(__name__)


# ============================================================
# CREATE NOTIFICATION
#
# farmer_id is supplied by a trusted caller.
#
# It is intentionally NOT accepted from the request body.
#
# This prevents a client from creating a notification
# for another farmer.
# ============================================================


def create_notification(
    repository: NotificationRepository,
    device_repository: DeviceTokenRepository,
    *,
    farmer_id: UUID,
    request: NotificationCreateRequest,
) -> Notification:

    notification = Notification(
        farmer_id=farmer_id,
        title=request.title,
        message=request.message,
        type=request.type,
        priority=request.priority,
        is_read=False,
    )

    created_notification = repository.create(
        notification,
    )

    # Push delivery must not roll back a persisted notification.
    try:
        device_tokens = device_repository.get_by_farmer(farmer_id)
        fids = [device_token.fid for device_token in device_tokens]

        if fids:
            stale_fids = send_push_notification(
                fids=fids,
                title=request.title,
                message=request.message,
            )

            if stale_fids:
                device_repository.delete_by_fids(stale_fids)

    except Exception:
        logger.exception(
            "Push notification delivery failed after notification creation."
        )

    return created_notification


# ============================================================
# GET NOTIFICATION
#
# Raises:
#     NotificationNotFoundError
#
# when the notification does not exist.
# ============================================================


def get_notification(
    repository: NotificationRepository,
    notification_id: UUID,
) -> Notification:

    notification = repository.get_by_id(
        notification_id,
    )

    if notification is None:
        raise NotificationNotFoundError()

    return notification


# ============================================================
# GET ALL NOTIFICATIONS
#
# Returns all notifications belonging to the farmer.
#
# Ordering is handled by the repository.
# ============================================================


def list_notifications(
    repository: NotificationRepository,
    farmer_id: UUID,
) -> list[Notification]:

    return repository.get_all_by_farmer(
        farmer_id,
    )


# ============================================================
# GET UNREAD NOTIFICATIONS
#
# Returns only unread notifications belonging
# to the farmer.
# ============================================================


def list_unread_notifications(
    repository: NotificationRepository,
    farmer_id: UUID,
) -> list[Notification]:

    return repository.get_unread_by_farmer(
        farmer_id,
    )


# ============================================================
# GET UNREAD COUNT
#
# Used by:
#
# - Notification badge
# - Dashboard
# - Mobile header
# ============================================================


def get_unread_notification_count(
    repository: NotificationRepository,
    farmer_id: UUID,
) -> int:

    return repository.count_unread_by_farmer(
        farmer_id,
    )


# ============================================================
# MARK ONE NOTIFICATION AS READ
#
# Idempotent operation.
#
# UNREAD
#     ↓
# READ
#
# READ
#     ↓
# READ
#
# If already read, no database update is performed.
# ============================================================


def mark_notification_read(
    repository: NotificationRepository,
    notification: Notification,
) -> Notification:

    if notification.is_read:
        return notification

    notification.is_read = True

    return repository.update(
        notification,
    )


# ============================================================
# MARK ALL NOTIFICATIONS AS READ
#
# Returns the number of notifications changed.
#
# Example:
#
# 5 unread
#     ↓
# mark_all_notifications_read()
#     ↓
# 5
#
# Calling again:
#
# 0 unread
#     ↓
# mark_all_notifications_read()
#     ↓
# 0
# ============================================================


def mark_all_notifications_read(
    repository: NotificationRepository,
    farmer_id: UUID,
) -> int:

    return repository.mark_all_read(
        farmer_id,
    )


# ============================================================
# DELETE NOTIFICATION
#
# Ownership/access checking is intentionally handled
# by the router before this function is called.
# ============================================================


def delete_notification(
    repository: NotificationRepository,
    notification: Notification,
) -> None:

    repository.delete(
        notification,
    )