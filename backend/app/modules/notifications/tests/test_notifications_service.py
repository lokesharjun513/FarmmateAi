from uuid import uuid4

import pytest

from app.modules.notifications.models import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.modules.notifications.models_device import DeviceToken
from app.modules.notifications.repository import (
    NotificationRepository,
)
from app.modules.notifications.repository_device import (
    DeviceTokenRepository,
)
from app.modules.notifications.schemas import (
    NotificationCreateRequest,
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
from app.shared.exceptions import (
    NotificationNotFoundError,
)

# ============================================================
# CREATE
# ============================================================


def test_create_notification(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    request = NotificationCreateRequest(
        title="Weather Alert",
        message="Heavy rain expected.",
        type=NotificationType.WEATHER,
        priority=NotificationPriority.HIGH,
    )

    result = create_notification(
        repository=repository,
        device_repository=DeviceTokenRepository(db),
        farmer_id=farmer_id,
        request=request,
    )

    assert result.id is not None
    assert result.farmer_id == farmer_id
    assert result.title == "Weather Alert"
    assert result.message == "Heavy rain expected."
    assert result.type == NotificationType.WEATHER
    assert result.priority == NotificationPriority.HIGH
    assert result.is_read is False


# ============================================================
# CREATE DEFAULT PRIORITY
# ============================================================


def test_create_notification_default_priority(db):

    repository = NotificationRepository(db)

    result = create_notification(
        repository=repository,
        device_repository=DeviceTokenRepository(db),
        farmer_id=uuid4(),
        request=NotificationCreateRequest(
            title="System",
            message="System message",
            type=NotificationType.SYSTEM,
        ),
    )

    assert result.priority == NotificationPriority.MEDIUM


# ============================================================
# GET
# ============================================================


def test_get_notification(db):

    repository = NotificationRepository(db)

    notification = Notification(
        farmer_id=uuid4(),
        title="Test",
        message="Test notification",
        type=NotificationType.SYSTEM,
    )

    repository.create(notification)

    result = get_notification(
        repository,
        notification.id,
    )

    assert result.id == notification.id


# ============================================================
# GET NOT FOUND
# ============================================================


def test_get_notification_not_found(db):

    repository = NotificationRepository(db)

    with pytest.raises(
        NotificationNotFoundError,
    ):

        get_notification(
            repository,
            uuid4(),
        )


# ============================================================
# LIST
# ============================================================


def test_list_notifications(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    for index in range(3):

        repository.create(
            Notification(
                farmer_id=farmer_id,
                title=f"Notification {index}",
                message="Message",
                type=NotificationType.SYSTEM,
            )
        )

    result = list_notifications(
        repository,
        farmer_id,
    )

    assert len(result) == 3


# ============================================================
# LIST EMPTY
# ============================================================


def test_list_notifications_empty(db):

    repository = NotificationRepository(db)

    result = list_notifications(
        repository,
        uuid4(),
    )

    assert result == []


# ============================================================
# LIST UNREAD
# ============================================================


def test_list_unread_notifications(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    unread = Notification(
        farmer_id=farmer_id,
        title="Unread",
        message="Message",
        type=NotificationType.SYSTEM,
        is_read=False,
    )

    read = Notification(
        farmer_id=farmer_id,
        title="Read",
        message="Message",
        type=NotificationType.SYSTEM,
        is_read=True,
    )

    repository.create(unread)
    repository.create(read)

    result = list_unread_notifications(
        repository,
        farmer_id,
    )

    assert len(result) == 1
    assert result[0].id == unread.id


# ============================================================
# UNREAD COUNT
# ============================================================


def test_get_unread_notification_count(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    for index in range(4):

        repository.create(
            Notification(
                farmer_id=farmer_id,
                title=f"Unread {index}",
                message="Message",
                type=NotificationType.SYSTEM,
                is_read=False,
            )
        )

    count = get_unread_notification_count(
        repository,
        farmer_id,
    )

    assert count == 4


# ============================================================
# MARK READ
# ============================================================


def test_mark_notification_read(db):

    repository = NotificationRepository(db)

    notification = Notification(
        farmer_id=uuid4(),
        title="Unread",
        message="Message",
        type=NotificationType.SYSTEM,
        is_read=False,
    )

    repository.create(notification)

    result = mark_notification_read(
        repository,
        notification,
    )

    assert result.is_read is True


# ============================================================
# MARK READ IDEMPOTENT
# ============================================================


def test_mark_notification_read_is_idempotent(db):

    repository = NotificationRepository(db)

    notification = Notification(
        farmer_id=uuid4(),
        title="Already Read",
        message="Message",
        type=NotificationType.SYSTEM,
        is_read=True,
    )

    repository.create(notification)

    result = mark_notification_read(
        repository,
        notification,
    )

    assert result.id == notification.id
    assert result.is_read is True


# ============================================================
# MARK ALL READ
# ============================================================


def test_mark_all_notifications_read(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    for index in range(3):

        repository.create(
            Notification(
                farmer_id=farmer_id,
                title=f"Notification {index}",
                message="Message",
                type=NotificationType.SYSTEM,
                is_read=False,
            )
        )

    result = mark_all_notifications_read(
        repository,
        farmer_id,
    )

    assert result == 3


# ============================================================
# MARK ALL READ EMPTY
# ============================================================


def test_mark_all_notifications_read_empty(db):

    repository = NotificationRepository(db)

    result = mark_all_notifications_read(
        repository,
        uuid4(),
    )

    assert result == 0


# ============================================================
# DELETE
# ============================================================


def test_delete_notification(db):

    repository = NotificationRepository(db)

    notification = Notification(
        farmer_id=uuid4(),
        title="Delete",
        message="Delete notification",
        type=NotificationType.SYSTEM,
    )

    repository.create(notification)

    notification_id = notification.id

    delete_notification(
        repository,
        notification,
    )

    assert repository.get_by_id(
        notification_id,
    ) is None


# ============================================================
# PUSH DELIVERY
# ============================================================


def test_create_notification_removes_stale_fids(
    db,
    monkeypatch,
):

    farmer_id = uuid4()
    repository = NotificationRepository(db)
    device_repository = DeviceTokenRepository(db)

    device_repository.create(
        DeviceToken(
            farmer_id=farmer_id,
            fid="stale-fid",
        )
    )

    monkeypatch.setattr(
        "app.modules.notifications.service.send_push_notification",
        lambda **kwargs: ["stale-fid"],
    )

    create_notification(
        repository=repository,
        device_repository=device_repository,
        farmer_id=farmer_id,
        request=NotificationCreateRequest(
            title="Weather",
            message="Rain expected.",
            type=NotificationType.WEATHER,
        ),
    )

    assert device_repository.get_by_fid("stale-fid") is None


def test_create_notification_survives_push_failure(
    db,
    monkeypatch,
):

    farmer_id = uuid4()
    repository = NotificationRepository(db)
    device_repository = DeviceTokenRepository(db)

    device_repository.create(
        DeviceToken(
            farmer_id=farmer_id,
            fid="fid-1",
        )
    )

    def fail_delivery(**kwargs):
        raise RuntimeError("FCM unavailable")

    monkeypatch.setattr(
        "app.modules.notifications.service.send_push_notification",
        fail_delivery,
    )

    result = create_notification(
        repository=repository,
        device_repository=device_repository,
        farmer_id=farmer_id,
        request=NotificationCreateRequest(
            title="Weather",
            message="Rain expected.",
            type=NotificationType.WEATHER,
        ),
    )

    assert result.id is not None
    assert repository.get_by_id(result.id) is not None
