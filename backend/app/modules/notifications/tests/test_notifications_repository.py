from uuid import uuid4

from app.modules.notifications.models import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.modules.notifications.repository import (
    NotificationRepository,
)


# ============================================================
# CREATE
# ============================================================


def test_create_notification(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    notification = Notification(
        farmer_id=farmer_id,
        title="Weather Alert",
        message="Rain expected tomorrow.",
        type=NotificationType.WEATHER,
        priority=NotificationPriority.HIGH,
        is_read=False,
    )

    result = repository.create(notification)

    assert result.id is not None
    assert result.farmer_id == farmer_id
    assert result.title == "Weather Alert"
    assert result.is_read is False


# ============================================================
# GET BY ID
# ============================================================


def test_get_by_id(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    notification = Notification(
        farmer_id=farmer_id,
        title="Test",
        message="Test notification",
        type=NotificationType.SYSTEM,
    )

    repository.create(notification)

    result = repository.get_by_id(notification.id)

    assert result is not None
    assert result.id == notification.id


# ============================================================
# GET BY ID NOT FOUND
# ============================================================


def test_get_by_id_not_found(db):

    repository = NotificationRepository(db)

    result = repository.get_by_id(uuid4())

    assert result is None


# ============================================================
# GET ALL BY FARMER
# ============================================================


def test_get_all_by_farmer(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    first = Notification(
        farmer_id=farmer_id,
        title="First",
        message="First notification",
        type=NotificationType.SYSTEM,
    )

    second = Notification(
        farmer_id=farmer_id,
        title="Second",
        message="Second notification",
        type=NotificationType.WEATHER,
    )

    repository.create(first)
    repository.create(second)

    results = repository.get_all_by_farmer(
        farmer_id,
    )

    assert len(results) == 2


# ============================================================
# FARMER ISOLATION
# ============================================================


def test_get_all_by_farmer_isolated(db):

    repository = NotificationRepository(db)

    farmer_one = uuid4()
    farmer_two = uuid4()

    repository.create(
        Notification(
            farmer_id=farmer_one,
            title="Farmer One",
            message="Notification",
            type=NotificationType.SYSTEM,
        )
    )

    repository.create(
        Notification(
            farmer_id=farmer_two,
            title="Farmer Two",
            message="Notification",
            type=NotificationType.SYSTEM,
        )
    )

    results = repository.get_all_by_farmer(
        farmer_one,
    )

    assert len(results) == 1
    assert results[0].farmer_id == farmer_one


# ============================================================
# GET UNREAD
# ============================================================


def test_get_unread_by_farmer(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    unread = Notification(
        farmer_id=farmer_id,
        title="Unread",
        message="Unread notification",
        type=NotificationType.SYSTEM,
        is_read=False,
    )

    read = Notification(
        farmer_id=farmer_id,
        title="Read",
        message="Read notification",
        type=NotificationType.SYSTEM,
        is_read=True,
    )

    repository.create(unread)
    repository.create(read)

    results = repository.get_unread_by_farmer(
        farmer_id,
    )

    assert len(results) == 1
    assert results[0].id == unread.id


# ============================================================
# COUNT UNREAD
# ============================================================


def test_count_unread_by_farmer(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    for index in range(3):

        repository.create(
            Notification(
                farmer_id=farmer_id,
                title=f"Notification {index}",
                message="Unread notification",
                type=NotificationType.SYSTEM,
                is_read=False,
            )
        )

    repository.create(
        Notification(
            farmer_id=farmer_id,
            title="Read",
            message="Read notification",
            type=NotificationType.SYSTEM,
            is_read=True,
        )
    )

    count = repository.count_unread_by_farmer(
        farmer_id,
    )

    assert count == 3


# ============================================================
# COUNT UNREAD EMPTY
# ============================================================


def test_count_unread_empty(db):

    repository = NotificationRepository(db)

    count = repository.count_unread_by_farmer(
        uuid4(),
    )

    assert count == 0


# ============================================================
# UPDATE
# ============================================================


def test_update_notification(db):

    repository = NotificationRepository(db)

    notification = Notification(
        farmer_id=uuid4(),
        title="Old Title",
        message="Old message",
        type=NotificationType.SYSTEM,
    )

    repository.create(notification)

    notification.title = "New Title"

    result = repository.update(notification)

    assert result.title == "New Title"


# ============================================================
# MARK ALL READ
# ============================================================


def test_mark_all_read(db):

    repository = NotificationRepository(db)

    farmer_id = uuid4()

    for index in range(3):

        repository.create(
            Notification(
                farmer_id=farmer_id,
                title=f"Notification {index}",
                message="Unread",
                type=NotificationType.SYSTEM,
                is_read=False,
            )
        )

    updated = repository.mark_all_read(
        farmer_id,
    )

    assert updated == 3

    unread_count = repository.count_unread_by_farmer(
        farmer_id,
    )

    assert unread_count == 0


# ============================================================
# MARK ALL READ ISOLATED
# ============================================================


def test_mark_all_read_only_affects_farmer(db):

    repository = NotificationRepository(db)

    farmer_one = uuid4()
    farmer_two = uuid4()

    repository.create(
        Notification(
            farmer_id=farmer_one,
            title="One",
            message="Unread",
            type=NotificationType.SYSTEM,
            is_read=False,
        )
    )

    repository.create(
        Notification(
            farmer_id=farmer_two,
            title="Two",
            message="Unread",
            type=NotificationType.SYSTEM,
            is_read=False,
        )
    )

    repository.mark_all_read(farmer_one)

    assert repository.count_unread_by_farmer(
        farmer_one,
    ) == 0

    assert repository.count_unread_by_farmer(
        farmer_two,
    ) == 1


# ============================================================
# MARK ALL READ WHEN NONE EXIST
# ============================================================


def test_mark_all_read_returns_zero_when_none_exist(db):

    repository = NotificationRepository(db)

    result = repository.mark_all_read(
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
        message="Delete me",
        type=NotificationType.SYSTEM,
    )

    repository.create(notification)

    notification_id = notification.id

    repository.delete(notification)

    result = repository.get_by_id(
        notification_id,
    )

    assert result is None