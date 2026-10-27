from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.chat.router import router
from app.modules.farmer.repository import FarmerRepository
from app.modules.chat.service import ChatService


# ============================================================
# TEST APP
# ============================================================

app = FastAPI()

app.include_router(router)


# ============================================================
# TEST IDS
# ============================================================

USER_ID = uuid4()
FARMER_ID = uuid4()


# ============================================================
# MOCK USER
# ============================================================

@pytest.fixture
def mock_user():

    return SimpleNamespace(
        id=USER_ID,
    )


# ============================================================
# MOCK FARMER
# ============================================================

@pytest.fixture
def mock_farmer():

    return SimpleNamespace(
        id=FARMER_ID,
        user_id=USER_ID,
    )


# ============================================================
# MOCK DATABASE
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
# FARMER REPOSITORY
# ============================================================

@pytest.fixture
def farmer_repository(
    monkeypatch,
    mock_farmer,
):

    monkeypatch.setattr(
        FarmerRepository,
        "get_by_user_id",
        lambda self, user_id: mock_farmer,
    )


# ============================================================
# CHAT SERVICE
# ============================================================

@pytest.fixture
def chat_service(monkeypatch):

    async def mock_chat(
        self,
        *,
        current_farmer,
        message,
    ):

        return "This is a test FarmMate AI response."

    monkeypatch.setattr(
        ChatService,
        "chat",
        mock_chat,
    )


# ============================================================
# SUCCESS
# ============================================================

def test_ask_fm_success(
    client,
    farmer_repository,
    chat_service,
):

    response = client.post(
        "/ask-fm",
        json={
            "message": "Should I irrigate my rice field today?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert (
        data["message"]
        == "AI response generated successfully."
    )

    assert (
        data["data"]["answer"]
        == "This is a test FarmMate AI response."
    )


# ============================================================
# FARMER NOT FOUND
# ============================================================

def test_ask_fm_farmer_not_found(
    client,
    monkeypatch,
):

    monkeypatch.setattr(
        FarmerRepository,
        "get_by_user_id",
        lambda self, user_id: None,
    )

    response = client.post(
        "/ask-fm",
        json={
            "message": "How is my crop?"
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert (
        data["detail"]
        == "Farmer profile not found."
    )


# ============================================================
# EMPTY MESSAGE
# ============================================================

def test_ask_fm_empty_message(
    client,
    farmer_repository,
):

    response = client.post(
        "/ask-fm",
        json={
            "message": ""
        },
    )

    assert response.status_code == 422


# ============================================================
# MESSAGE TOO LONG
# ============================================================

def test_ask_fm_message_too_long(
    client,
    farmer_repository,
):

    response = client.post(
        "/ask-fm",
        json={
            "message": "A" * 2001
        },
    )

    assert response.status_code == 422


# ============================================================
# MESSAGE MAX LENGTH
# ============================================================

def test_ask_fm_message_max_length(
    client,
    farmer_repository,
    chat_service,
):

    response = client.post(
        "/ask-fm",
        json={
            "message": "A" * 2000
        },
    )

    assert response.status_code == 200


# ============================================================
# MISSING MESSAGE
# ============================================================

def test_ask_fm_missing_message(
    client,
):

    response = client.post(
        "/ask-fm",
        json={},
    )

    assert response.status_code == 422