from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db
from app.modules.scheduler.router import router


# ============================================================
# TEST APP
# ============================================================


app = FastAPI()

app.include_router(router)


# ============================================================
# TEST USER
# ============================================================


USER_ID = uuid4()


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

    return MagicMock()


# ============================================================
# CLIENT
# ============================================================


@pytest.fixture
def client(mock_user, db):

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

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


# ============================================================
# RUN SCHEDULER
# ============================================================


def test_run_scheduler(
    client,
    monkeypatch,
):

    result = SimpleNamespace(
        processed_farms=5,
        processed_crop_seasons=4,
        weather_updated=3,
        advisor_generated=4,
        notifications_created=4,
        expired_sessions=2,
        completed=True,
    )

    service = MagicMock()

    service.run = AsyncMock(
        return_value=result,
    )

    monkeypatch.setattr(
        "app.modules.scheduler.router.SchedulerService",
        MagicMock(return_value=service),
    )

    response = client.post(
        "/scheduler/run",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Scheduler executed successfully."
    )

    assert body["data"]["processed_farms"] == 5
    assert body["data"]["processed_crop_seasons"] == 4
    assert body["data"]["weather_updated"] == 3
    assert body["data"]["advisor_generated"] == 4
    assert body["data"]["notifications_created"] == 4
    assert body["data"]["expired_sessions"] == 2
    assert body["data"]["completed"] is True

    service.run.assert_awaited_once()


# ============================================================
# AUTHENTICATION REQUIRED
# ============================================================


def test_run_scheduler_requires_authentication():

    unauthenticated_app = FastAPI()

    unauthenticated_app.include_router(router)

    async def reject_auth():

        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    unauthenticated_app.dependency_overrides[
        get_current_user
    ] = reject_auth

    client = TestClient(
        unauthenticated_app,
    )

    response = client.post(
        "/scheduler/run",
    )

    assert response.status_code == 401