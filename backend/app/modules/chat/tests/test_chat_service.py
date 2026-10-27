from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.ai_engine.providers.ai_provider import AIProviderError
from app.modules.chat.service import ChatService

# ============================================================
# HELPERS
# ============================================================

def create_farmer():

    return SimpleNamespace(
        id=uuid4(),
    )


def create_session():

    return SimpleNamespace(
        id=uuid4(),
    )


# ============================================================
# MOCK DEPENDENCIES
# ============================================================

class MockContextBuilder:

    def __init__(self, *args, **kwargs):

        pass

    async def build(self, farmer):

        return SimpleNamespace(
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


class MockSessionService:

    def __init__(self, *args, **kwargs):

        self.refresh_count = 0

    def get_or_create_session(self, farmer):

        return create_session()

    def refresh_session(self, session):

        self.refresh_count += 1

        return session


class MockMessageRepository:

    def __init__(self):

        self.user_messages = []
        self.assistant_messages = []

    def create_user_message(
        self,
        *,
        session_id,
        content,
    ):

        self.user_messages.append(
            {
                "session_id": session_id,
                "content": content,
            }
        )

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

        self.assistant_messages.append(
            {
                "session_id": session_id,
                "content": content,
            }
        )


class MockPlanner:

    async def ask(
        self,
        *,
        context,
        history,
        question,
    ):

        return "Irrigate the field in the morning."


# ============================================================
# FACTORY
# ============================================================

def create_service():

    service = ChatService.__new__(
        ChatService,
    )

    service.context_builder = MockContextBuilder()

    service.session_service = MockSessionService()

    service.message_repository = MockMessageRepository()

    service.planner = MockPlanner()

    return service


# ============================================================
# SUCCESS
# ============================================================

@pytest.mark.asyncio
async def test_chat_success():

    service = create_service()

    farmer = create_farmer()

    answer = await service.chat(
        current_farmer=farmer,
        message="Should I irrigate today?",
    )

    assert answer == (
        "Irrigate the field in the morning."
    )


# ============================================================
# USER MESSAGE SAVED
# ============================================================

@pytest.mark.asyncio
async def test_user_message_is_saved():

    service = create_service()

    farmer = create_farmer()

    await service.chat(
        current_farmer=farmer,
        message="Should I irrigate today?",
    )

    assert len(
        service.message_repository.user_messages
    ) == 1

    assert (
        service.message_repository.user_messages[0][
            "content"
        ]
        == "Should I irrigate today?"
    )


# ============================================================
# ASSISTANT MESSAGE SAVED
# ============================================================

@pytest.mark.asyncio
async def test_assistant_message_is_saved():

    service = create_service()

    farmer = create_farmer()

    await service.chat(
        current_farmer=farmer,
        message="Should I irrigate today?",
    )

    assert len(
        service.message_repository.assistant_messages
    ) == 1

    assert (
        service.message_repository.assistant_messages[0][
            "content"
        ]
        == "Irrigate the field in the morning."
    )


# ============================================================
# MESSAGE IS STRIPPED
# ============================================================

@pytest.mark.asyncio
async def test_message_is_stripped():

    service = create_service()

    farmer = create_farmer()

    await service.chat(
        current_farmer=farmer,
        message="   Should I irrigate?   ",
    )

    assert (
        service.message_repository.user_messages[0][
            "content"
        ]
        == "Should I irrigate?"
    )


# ============================================================
# HISTORY
# ============================================================

@pytest.mark.asyncio
async def test_history_excludes_current_message():

    service = create_service()

    previous_message = SimpleNamespace(
        role=SimpleNamespace(value="assistant"),
        content="Previous answer",
    )

    service.message_repository.get_recent_messages = (
        lambda session_id, limit: [previous_message]
    )

    captured = {}

    class CapturingPlanner:

        async def ask(
            self,
            *,
            context,
            history,
            question,
        ):

            captured["history"] = history

            return "Current answer"

    service.planner = CapturingPlanner()

    await service.chat(
        current_farmer=create_farmer(),
        message="Should I irrigate today?",
    )

    assert "assistant: Previous answer" in captured["history"]

    assert (
        "Should I irrigate today?"
        not in captured["history"]
    )


# ============================================================
# EMPTY MESSAGE
# ============================================================

@pytest.mark.asyncio
async def test_empty_message_fails():

    service = create_service()

    farmer = create_farmer()

    with pytest.raises(ValueError):

        await service.chat(
            current_farmer=farmer,
            message="   ",
        )


# ============================================================
# AI EMPTY RESPONSE
# ============================================================

@pytest.mark.asyncio
async def test_empty_ai_response():

    service = create_service()

    class EmptyPlanner:

        async def ask(
            self,
            *,
            context,
            history,
            question,
        ):

            return ""

    service.planner = EmptyPlanner()

    farmer = create_farmer()

    with pytest.raises(
        AIProviderError,
        match="AI returned an empty response.",
    ):

        await service.chat(
            current_farmer=farmer,
            message="How is my crop?",
        )

    assert (
        service.message_repository.assistant_messages
        == []
    )


# ============================================================
# AI PROVIDER FAILURE
# ============================================================

@pytest.mark.asyncio
async def test_ai_provider_failure_is_not_hidden():

    service = create_service()

    class FailingPlanner:

        async def ask(
            self,
            *,
            context,
            history,
            question,
        ):

            raise AIProviderError(
                "AI service unavailable."
            )

    service.planner = FailingPlanner()

    farmer = create_farmer()

    with pytest.raises(
        AIProviderError,
        match="AI service unavailable.",
    ):

        await service.chat(
            current_farmer=farmer,
            message="How is my crop?",
        )

    assert (
        service.message_repository.assistant_messages
        == []
    )

    assert (
        service.session_service.refresh_count
        == 1
    )


# ============================================================
# SESSION REFRESHED
# ============================================================

@pytest.mark.asyncio
async def test_session_refreshed():

    service = create_service()

    farmer = create_farmer()

    await service.chat(
        current_farmer=farmer,
        message="How is my crop?",
    )

    assert (
        service.session_service.refresh_count
        == 1
    )