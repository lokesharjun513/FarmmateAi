from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db
from app.modules.notifications.router import router

# ============================================================
# TEST APP
# ============================================================


app = FastAPI()

app.include_router(
    router,
    prefix="/api/v1",
)


# ============================================================
# TEST IDS
# ============================================================


USER_ID = uuid4()
FARMER_ID = uuid4()


# ============================================================
# TEST USER
# ============================================================


@pytest.fixture
def mock_user():

    return SimpleNamespace(
        id=USER_ID,
    )


# ============================================================
# TEST DATABASE
# ============================================================


@pytest.fixture
def db():

    return SimpleNamespace()


# ============================================================
# TEST FARMER
# ============================================================


@pytest.fixture
def farmer():

    return SimpleNamespace(
        id=FARMER_ID,
        user_id=USER_ID,
    )


# ============================================================
# CLIENT
# ============================================================


@pytest.fixture
def client(
    mock_user,
    db,
    farmer,
    monkeypatch,
):

    def override_current_user():

        return mock_user

    def override_db():

        yield db

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    app.dependency_overrides[
        get_db
    ] = override_db

    monkeypatch.setattr(
        "app.modules.notifications.router.FarmerRepository.get_by_user_id",
        lambda self, user_id: farmer,
    )

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


# ============================================================
# CREATE
# ============================================================


def test_create_notification(
    client,
    monkeypatch,
):

    notification = SimpleNamespace(
        id=uuid4(),
        farmer_id=FARMER_ID,
        title="Weather Alert",
        message="Rain expected tomorrow.",
        type="WEATHER",
        priority="HIGH",
        is_read=False,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.create_notification",
        lambda repository, device_repository, farmer_id, request:
            notification,
    )

    response = client.post(
        "/api/v1/notifications",
        json={
            "title": "Weather Alert",
            "message": "Rain expected tomorrow.",
            "type": "WEATHER",
            "priority": "HIGH",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["data"]["title"] == "Weather Alert"
    assert body["data"]["farmer_id"] == str(FARMER_ID)


# ============================================================
# CREATE INVALID REQUEST
# ============================================================


def test_create_notification_invalid_request(
    client,
):

    response = client.post(
        "/api/v1/notifications",
        json={
            "title": "",
            "message": "Message",
            "type": "SYSTEM",
        },
    )

    assert response.status_code == 422


# ============================================================
# CREATE WITH FARMER ID
#
# Client must not be allowed to select farmer.
# ============================================================


def test_create_notification_rejects_farmer_id(
    client,
):

    response = client.post(
        "/api/v1/notifications",
        json={
            "title": "Test",
            "message": "Test message",
            "type": "SYSTEM",
            "farmer_id": str(uuid4()),
        },
    )

    assert response.status_code == 422


# ============================================================
# LIST
# ============================================================


def test_list_notifications(
    client,
    monkeypatch,
):

    notifications = [
        SimpleNamespace(
            id=uuid4(),
            farmer_id=FARMER_ID,
            title="Weather",
            message="Rain expected.",
            type="WEATHER",
            priority="MEDIUM",
            is_read=False,
            created_at="2026-08-16T08:00:00",
            updated_at="2026-08-16T08:00:00",
        ),
    ]

    monkeypatch.setattr(
        "app.modules.notifications.router.list_notifications",
        lambda repository, farmer_id:
            notifications,
    )

    response = client.get(
        "/api/v1/notifications",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1


# ============================================================
# UNREAD
# ============================================================


def test_list_unread_notifications(
    client,
    monkeypatch,
):

    notifications = [
        SimpleNamespace(
            id=uuid4(),
            farmer_id=FARMER_ID,
            title="Unread",
            message="Unread notification.",
            type="SYSTEM",
            priority="HIGH",
            is_read=False,
            created_at="2026-08-16T08:00:00",
            updated_at="2026-08-16T08:00:00",
        ),
    ]

    monkeypatch.setattr(
        "app.modules.notifications.router.list_unread_notifications",
        lambda repository, farmer_id:
            notifications,
    )

    response = client.get(
        "/api/v1/notifications/unread",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["is_read"] is False


# ============================================================
# UNREAD COUNT
# ============================================================


def test_unread_notification_count(
    client,
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.notifications.router.get_unread_notification_count",
        lambda repository, farmer_id: 5,
    )

    response = client.get(
        "/api/v1/notifications/unread-count",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["unread_count"] == 5


# ============================================================
# MARK ALL READ
# ============================================================


def test_mark_all_notifications_read(
    client,
    monkeypatch,
):

    called = {}

    def mock_mark_all(
        repository,
        farmer_id,
    ):

        called["farmer_id"] = farmer_id

        return 3

    monkeypatch.setattr(
        "app.modules.notifications.router.mark_all_notifications_read",
        mock_mark_all,
    )

    response = client.patch(
        "/api/v1/notifications/read-all",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert called["farmer_id"] == FARMER_ID


# ============================================================
# GET BY ID
# ============================================================


def test_get_notification(
    client,
    monkeypatch,
):

    notification_id = uuid4()

    notification = SimpleNamespace(
        id=notification_id,
        farmer_id=FARMER_ID,
        title="Test",
        message="Test notification.",
        type="SYSTEM",
        priority="MEDIUM",
        is_read=False,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.get_notification",
        lambda repository, notification_id:
            notification,
    )

    response = client.get(
        f"/api/v1/notifications/{notification_id}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == str(notification_id)


# ============================================================
# GET NOT FOUND
# ============================================================


def test_get_notification_not_found(
    client,
    monkeypatch,
):

    from app.shared.exceptions import (
        NotificationNotFoundError,
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.get_notification",
        lambda repository, notification_id:
            (_ for _ in ()).throw(
                NotificationNotFoundError()
            ),
    )

    response = client.get(
        f"/api/v1/notifications/{uuid4()}",
    )

    assert response.status_code == 404


# ============================================================
# GET OTHER FARMER NOTIFICATION
# ============================================================


def test_get_notification_access_denied(
    client,
    monkeypatch,
):

    notification = SimpleNamespace(
        id=uuid4(),
        farmer_id=uuid4(),
        title="Private",
        message="Private notification.",
        type="SYSTEM",
        priority="MEDIUM",
        is_read=False,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.get_notification",
        lambda repository, notification_id:
            notification,
    )

    response = client.get(
        f"/api/v1/notifications/{notification.id}",
    )

    assert response.status_code == 403


# ============================================================
# MARK READ
# ============================================================


def test_mark_notification_read(
    client,
    monkeypatch,
):

    notification_id = uuid4()

    notification = SimpleNamespace(
        id=notification_id,
        farmer_id=FARMER_ID,
        title="Unread",
        message="Notification.",
        type="SYSTEM",
        priority="MEDIUM",
        is_read=False,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    updated_notification = SimpleNamespace(
        id=notification_id,
        farmer_id=FARMER_ID,
        title="Unread",
        message="Notification.",
        type="SYSTEM",
        priority="MEDIUM",
        is_read=True,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.get_notification",
        lambda repository, notification_id:
            notification,
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.mark_notification_read",
        lambda repository, notification:
            updated_notification,
    )

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/read",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["is_read"] is True


# ============================================================
# MARK READ OTHER FARMER
# ============================================================


def test_mark_notification_read_access_denied(
    client,
    monkeypatch,
):

    notification = SimpleNamespace(
        id=uuid4(),
        farmer_id=uuid4(),
        title="Private",
        message="Private notification.",
        type="SYSTEM",
        priority="MEDIUM",
        is_read=False,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.get_notification",
        lambda repository, notification_id:
            notification,
    )

    response = client.patch(
        f"/api/v1/notifications/{notification.id}/read",
    )

    assert response.status_code == 403


# ============================================================
# DELETE
# ============================================================


def test_delete_notification(
    client,
    monkeypatch,
):

    notification = SimpleNamespace(
        id=uuid4(),
        farmer_id=FARMER_ID,
        title="Delete",
        message="Delete notification.",
        type="SYSTEM",
        priority="LOW",
        is_read=False,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    called = {}

    monkeypatch.setattr(
        "app.modules.notifications.router.get_notification",
        lambda repository, notification_id:
            notification,
    )

    def mock_delete(
        repository,
        notification,
    ):

        called["id"] = notification.id

    monkeypatch.setattr(
        "app.modules.notifications.router.delete_notification",
        mock_delete,
    )

    response = client.delete(
        f"/api/v1/notifications/{notification.id}",
    )

    assert response.status_code == 204
    assert called["id"] == notification.id


# ============================================================
# DELETE OTHER FARMER
# ============================================================


def test_delete_notification_access_denied(
    client,
    monkeypatch,
):

    notification = SimpleNamespace(
        id=uuid4(),
        farmer_id=uuid4(),
        title="Private",
        message="Private notification.",
        type="SYSTEM",
        priority="LOW",
        is_read=False,
        created_at="2026-08-16T08:00:00",
        updated_at="2026-08-16T08:00:00",
    )

    monkeypatch.setattr(
        "app.modules.notifications.router.get_notification",
        lambda repository, notification_id:
            notification,
    )

    response = client.delete(
        f"/api/v1/notifications/{notification.id}",
    )

    assert response.status_code == 403


# ============================================================
# DEVICE REGISTRATION
# ============================================================


def test_register_device_fid(
    client,
    monkeypatch,
):

    called = {}

    def mock_register(
        db,
        farmer_id,
        fid,
        device_name=None,
    ):

        called["farmer_id"] = farmer_id
        called["fid"] = fid
        called["device_name"] = device_name

    monkeypatch.setattr(
        "app.modules.notifications.router.register_device_token",
        mock_register,
    )

    response = client.post(
        "/api/v1/notifications/devices",
        json={
            "fid": "fid-1",
            "device_name": "Android",
        },
    )

    assert response.status_code == 201
    assert response.json()["success"] is True
    assert called == {
        "farmer_id": FARMER_ID,
        "fid": "fid-1",
        "device_name": "Android",
    }


def test_register_device_fid_validates_empty_fid(client):

    response = client.post(
        "/api/v1/notifications/devices",
        json={"fid": "   "},
    )

    assert response.status_code == 422


# ============================================================
# DEVICE DEACTIVATION
# ============================================================


def test_deactivate_device_fid(
    client,
    monkeypatch,
):

    called = {}

    def mock_deactivate(
        db,
        farmer_id,
        fid,
    ):

        called["farmer_id"] = farmer_id
        called["fid"] = fid

    monkeypatch.setattr(
        "app.modules.notifications.router.deactivate_device_token",
        mock_deactivate,
    )

    response = client.delete(
        "/api/v1/notifications/devices/fid-1",
    )

    assert response.status_code == 204
    assert called == {
        "farmer_id": FARMER_ID,
        "fid": "fid-1",
    }


# ============================================================
# AUTHENTICATION
# ============================================================


def test_list_notifications_requires_authentication():

    app.dependency_overrides.clear()

    client = TestClient(app)

    response = client.get(
        "/api/v1/notifications",
    )

    assert response.status_code in (
        401,
        403,
    )