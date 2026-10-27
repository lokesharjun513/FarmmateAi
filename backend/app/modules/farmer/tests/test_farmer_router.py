from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db
from app.modules.farmer.router import router


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

    return SimpleNamespace()


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
# CREATE PROFILE
# ============================================================


def test_create_farmer_profile(
    client,
    monkeypatch,
):

    farmer = SimpleNamespace(
        id=uuid4(),
        user_id=USER_ID,
        preferred_language="Telugu",
        experience_years=5,
        profile_completion=0,
        onboarding_completed=False,
    )

    monkeypatch.setattr(
        "app.modules.farmer.router.create_farmer_profile",
        lambda repository, user_id, request:
            farmer,
    )

    response = client.post(
        "/farmer/profile",
        json={
            "preferred_language": "Telugu",
            "experience_years": 5,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == (
        "Farmer profile created successfully."
    )

    assert body["data"]["user_id"] == str(USER_ID)
    assert body["data"]["preferred_language"] == "Telugu"
    assert body["data"]["experience_years"] == 5


# ============================================================
# CREATE PROFILE - DEFAULT VALUES
# ============================================================


def test_create_farmer_profile_defaults(
    client,
    monkeypatch,
):

    farmer = SimpleNamespace(
        id=uuid4(),
        user_id=USER_ID,
        preferred_language="English",
        experience_years=None,
        profile_completion=0,
        onboarding_completed=False,
    )

    monkeypatch.setattr(
        "app.modules.farmer.router.create_farmer_profile",
        lambda repository, user_id, request:
            farmer,
    )

    response = client.post(
        "/farmer/profile",
        json={},
    )

    assert response.status_code == 201

    data = response.json()["data"]

    assert data["preferred_language"] == "English"
    assert data["experience_years"] is None


# ============================================================
# CREATE PROFILE - INVALID REQUEST
# ============================================================


def test_create_farmer_profile_invalid_request(
    client,
):

    response = client.post(
        "/farmer/profile",
        json={
            "preferred_language": "",
        },
    )

    assert response.status_code == 422


# ============================================================
# GET PROFILE
# ============================================================


def test_get_farmer_profile(
    client,
    monkeypatch,
):

    farmer = SimpleNamespace(
        id=uuid4(),
        user_id=USER_ID,
        preferred_language="Telugu",
        experience_years=10,
        profile_completion=50,
        onboarding_completed=False,
    )

    monkeypatch.setattr(
        "app.modules.farmer.router.get_farmer_profile",
        lambda repository, user_id:
            farmer,
    )

    response = client.get(
        "/farmer/profile",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Farmer profile retrieved successfully."
    )

    assert body["data"]["id"] == str(farmer.id)
    assert body["data"]["user_id"] == str(USER_ID)
    assert body["data"]["preferred_language"] == "Telugu"
    assert body["data"]["experience_years"] == 10


# ============================================================
# UPDATE PROFILE
# ============================================================


def test_update_farmer_profile(
    client,
    monkeypatch,
):

    farmer = SimpleNamespace(
        id=uuid4(),
        user_id=USER_ID,
        preferred_language="Hindi",
        experience_years=15,
        profile_completion=50,
        onboarding_completed=False,
    )

    monkeypatch.setattr(
        "app.modules.farmer.router.update_farmer_profile",
        lambda repository, user_id, request:
            farmer,
    )

    response = client.patch(
        "/farmer/profile",
        json={
            "preferred_language": "Hindi",
            "experience_years": 15,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Farmer profile updated successfully."
    )

    assert body["data"]["preferred_language"] == "Hindi"
    assert body["data"]["experience_years"] == 15


# ============================================================
# UPDATE PROFILE - EMPTY REQUEST
# ============================================================


def test_update_farmer_profile_empty_request(
    client,
    monkeypatch,
):

    farmer = SimpleNamespace(
        id=uuid4(),
        user_id=USER_ID,
        preferred_language="English",
        experience_years=None,
        profile_completion=0,
        onboarding_completed=False,
    )

    monkeypatch.setattr(
        "app.modules.farmer.router.update_farmer_profile",
        lambda repository, user_id, request:
            farmer,
    )

    response = client.patch(
        "/farmer/profile",
        json={},
    )

    assert response.status_code == 200


# ============================================================
# UPDATE PROFILE - INVALID EXPERIENCE
# ============================================================


def test_update_farmer_profile_invalid_experience(
    client,
):

    response = client.patch(
        "/farmer/profile",
        json={
            "experience_years": -1,
        },
    )

    assert response.status_code == 422


# ============================================================
# AUTHENTICATION REQUIRED
# ============================================================


def test_create_profile_requires_authentication(
    db,
):

    unauthenticated_app = FastAPI()

    unauthenticated_app.include_router(router)

    def override_db():
        yield db

    unauthenticated_app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(
        unauthenticated_app,
    )

    response = client.post(
        "/farmer/profile",
        json={
            "preferred_language": "Telugu",
            "experience_years": 5,
        },
    )

    assert response.status_code == 401


# ============================================================
# GET PROFILE REQUIRES AUTHENTICATION
# ============================================================


def test_get_profile_requires_authentication(
    db,
):

    unauthenticated_app = FastAPI()

    unauthenticated_app.include_router(router)

    def override_db():
        yield db

    unauthenticated_app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(
        unauthenticated_app,
    )

    response = client.get(
        "/farmer/profile",
    )

    assert response.status_code == 401


# ============================================================
# PATCH PROFILE REQUIRES AUTHENTICATION
# ============================================================


def test_update_profile_requires_authentication(
    db,
):

    unauthenticated_app = FastAPI()

    unauthenticated_app.include_router(router)

    def override_db():
        yield db

    unauthenticated_app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(
        unauthenticated_app,
    )

    response = client.patch(
        "/farmer/profile",
        json={
            "preferred_language": "Telugu",
        },
    )

    assert response.status_code == 401