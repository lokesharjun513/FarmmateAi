from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User


BASE_URL = "/api/v1/auth"


# ============================================================
# HELPERS
# ============================================================


def create_user(
    db,
    *,
    full_name="Test Farmer",
    mobile="9876543210",
    email="test@example.com",
    password_hash="hashed-password",
    is_active=True,
):

    user = User(
        id=uuid4(),
        full_name=full_name,
        mobile=mobile,
        email=email,
        password_hash=password_hash,
        is_active=is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def client(db):

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(db):

    user = create_user(
        db,
        password_hash="unused",
    )

    def override_db():
        yield db

    def override_current_user():
        return user

    app.dependency_overrides[get_db] = override_db

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    client = TestClient(app)

    yield client, user

    app.dependency_overrides.clear()


# ============================================================
# REGISTER
# ============================================================


def test_register(client):

    response = client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "Test Farmer",
            "mobile": "9876543210",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == (
        "User registered successfully."
    )

    assert body["data"]["full_name"] == "Test Farmer"
    assert body["data"]["mobile"] == "9876543210"
    assert body["data"]["email"] == "test@example.com"
    assert body["data"]["is_active"] is True

    assert "password" not in body["data"]
    assert "password_hash" not in body["data"]


def test_register_duplicate_email(client):

    first = client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "First User",
            "mobile": "9876543210",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert first.status_code == 200

    second = client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "Second User",
            "mobile": "9999999999",
            "email": "TEST@EXAMPLE.COM",
            "password": "password123",
        },
    )

    assert second.status_code == 409


def test_register_duplicate_mobile(client):

    first = client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "First User",
            "mobile": "9876543210",
            "email": "first@example.com",
            "password": "password123",
        },
    )

    assert first.status_code == 200

    second = client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "Second User",
            "mobile": "9876543210",
            "email": "second@example.com",
            "password": "password123",
        },
    )

    assert second.status_code == 409


def test_register_invalid_request(client):

    response = client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "A",
            "mobile": "123",
            "email": "invalid",
            "password": "123",
        },
    )

    assert response.status_code == 422


# ============================================================
# LOGIN
# ============================================================


def test_login_with_email(client):

    register_response = client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "Test Farmer",
            "mobile": "9876543210",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 200

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "identifier": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Login successful."
    assert body["data"]["access_token"]
    assert body["data"]["token_type"] == "bearer"


def test_login_with_mobile(client):

    client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "Test Farmer",
            "mobile": "9876543210",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "identifier": "9876543210",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["access_token"]


def test_login_wrong_password(client):

    client.post(
        f"{BASE_URL}/register",
        json={
            "full_name": "Test Farmer",
            "mobile": "9876543210",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "identifier": "test@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_login_unknown_user(client):

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "identifier": "missing@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401


def test_login_invalid_request(client):

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "identifier": "",
            "password": "",
        },
    )

    assert response.status_code == 422


# ============================================================
# ME
# ============================================================


def test_get_me(
    authenticated_client,
):

    client, user = authenticated_client

    response = client.get(
        f"{BASE_URL}/me",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == (
        "User retrieved successfully."
    )

    assert body["data"]["id"] == str(user.id)
    assert body["data"]["full_name"] == user.full_name
    assert body["data"]["mobile"] == user.mobile
    assert body["data"]["email"] == user.email
    assert body["data"]["is_active"] is True


def test_get_me_requires_authentication(
    client,
):

    response = client.get(
        f"{BASE_URL}/me",
    )

    assert response.status_code == 401


def test_get_me_does_not_expose_password(
    authenticated_client,
):

    client, _ = authenticated_client

    response = client.get(
        f"{BASE_URL}/me",
    )

    body = response.json()

    assert "password" not in body["data"]
    assert "password_hash" not in body["data"]