from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.auth import get_current_user
from app.core.exception_handlers import register_exception_handlers
from app.database.session import get_db
from app.modules.ai_engine.context import AIContext
from app.modules.chat.chat_planner import ChatPlanner
from app.modules.chat.router import router
from app.modules.chat.service import ChatService
from app.modules.farmer.repository import FarmerRepository

# ============================================================
# MOCKS
# ============================================================


class MockResponse:

    def __init__(
        self,
        data,
        status_code=200,
    ):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):

        if self.status_code >= 400:

            request = httpx.Request(
                "POST",
                "http://localhost:20128/v1/chat/completions",
            )

            response = httpx.Response(
                self.status_code,
                request=request,
            )

            raise httpx.HTTPStatusError(
                "HTTP error",
                request=request,
                response=response,
            )

    def json(self):

        return self._data


class MockAsyncClient:

    def __init__(
        self,
        *,
        data=None,
        status_code=200,
    ):
        self.data = data or {
            "choices": [
                {
                    "message": {
                        "content": "Hello! How can I help you"
                    }
                }
            ]
        }
        self.status_code = status_code

        self.url = None
        self.headers = None
        self.payload = None

    async def __aenter__(self):

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):

        return False

    async def post(
        self,
        url,
        *,
        headers,
        json,
    ):

        self.url = url
        self.headers = headers
        self.payload = json

        return MockResponse(
            self.data,
            status_code=self.status_code,
        )


class FakeContextBuilder:

    def __init__(self, *args, **kwargs):

        pass

    async def build(self, farmer):

        return AIContext(
            crop_name="Rice",
            crop_variety="BPT 5204",
            crop_age_days=45,
            soil_type="Clay",
            location="Nellore, Andhra Pradesh",
            weather="Clear Sky",
            temperature=32.5,
            humidity=70,
            rain_probability=20,
            today_activities=[
                "Irrigate field",
            ],
        )


class FakeSessionService:

    def __init__(self, *args, **kwargs):

        self.refresh_count = 0

    def get_or_create_session(self, farmer):

        return SimpleNamespace(
            id=uuid4(),
        )

    def refresh_session(self, session):

        self.refresh_count += 1

        return session


class FakeMessageRepository:

    def __init__(self, *args, **kwargs):

        self.user_messages = []
        self.assistant_messages = []

    def create_user_message(
        self,
        *,
        session_id,
        content,
    ):

        self.user_messages.append(content)

    def get_recent_messages(
        self,
        session_id,
        limit,
    ):

        return []

    def create_assistant_message(
        self,
        *,
        session_id,
        content,
    ):

        self.assistant_messages.append(content)


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def app_client(monkeypatch):

    captured = {}

    def fake_chat_service_init(
        self,
        *args,
        **kwargs,
    ):

        self.context_builder = FakeContextBuilder()
        self.session_service = FakeSessionService()
        self.message_repository = FakeMessageRepository()
        self.planner = ChatPlanner()

        captured["service"] = self

    monkeypatch.setattr(
        ChatService,
        "__init__",
        fake_chat_service_init,
    )

    user = SimpleNamespace(
        id=uuid4(),
    )

    farmer = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
    )

    monkeypatch.setattr(
        FarmerRepository,
        "get_by_user_id",
        lambda self, user_id: farmer,
    )

    app = FastAPI()

    app.include_router(
        router,
        prefix="/api/v1",
    )

    register_exception_handlers(app)

    app.dependency_overrides[
        get_current_user
    ] = lambda: user

    app.dependency_overrides[
        get_db
    ] = lambda: SimpleNamespace()

    yield TestClient(app), captured


@pytest.fixture
def configured_ai(monkeypatch):

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_API_URL",
        "http://localhost:20128/v1",
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_API_KEY",
        SecretStr("test-api-key"),
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_MODEL",
        "static-best-coding",
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_TEMPERATURE",
        0.2,
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_MAX_TOKENS",
        500,
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_REQUEST_TIMEOUT",
        30.0,
    )


# ============================================================
# SUCCESS
# ============================================================


def test_ask_fm_generates_answer_from_provider(
    app_client,
    configured_ai,
    monkeypatch,
):

    client, captured = app_client

    mock_client = MockAsyncClient()

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: mock_client,
    )

    response = client.post(
        "/api/v1/ask-fm",
        json={
            "message": "Hi",
            "farm_id": str(uuid4()),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["data"]["answer"] == (
        "Hello! How can I help you"
    )

    assert mock_client.url == (
        "http://localhost:20128/v1/chat/completions"
    )

    assert mock_client.headers["Authorization"] == (
        "Bearer test-api-key"
    )

    assert mock_client.payload["model"] == (
        "static-best-coding"
    )

    assert mock_client.payload["messages"][1]["content"].find(
        "Hi"
    ) >= 0

    service = captured["service"]

    assert (
        service.message_repository.user_messages
        == ["Hi"]
    )

    assert (
        service.message_repository.assistant_messages
        == ["Hello! How can I help you"]
    )

    assert service.session_service.refresh_count == 1


# ============================================================
# PROVIDER FAILURE
# ============================================================


def test_ask_fm_returns_bad_gateway_on_provider_failure(
    app_client,
    configured_ai,
    monkeypatch,
):

    client, captured = app_client

    mock_client = MockAsyncClient(
        data={"error": "invalid api key"},
        status_code=401,
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: mock_client,
    )

    response = client.post(
        "/api/v1/ask-fm",
        json={
            "message": "Hi",
            "farm_id": str(uuid4()),
        },
    )

    assert response.status_code == 502

    data = response.json()

    assert data["success"] is False
    assert data["message"] == (
        "AI service is temporarily unavailable. "
        "Please try again."
    )

    service = captured["service"]

    assert service.message_repository.assistant_messages == []


def test_ask_fm_returns_bad_gateway_on_empty_provider_content(
    app_client,
    configured_ai,
    monkeypatch,
):

    client, captured = app_client

    mock_client = MockAsyncClient(
        data={
            "choices": [
                {
                    "message": {
                        "content": "   "
                    }
                }
            ]
        },
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: mock_client,
    )

    response = client.post(
        "/api/v1/ask-fm",
        json={
            "message": "Hi",
            "farm_id": str(uuid4()),
        },
    )

    assert response.status_code == 502

    service = captured["service"]

    assert service.message_repository.assistant_messages == []
