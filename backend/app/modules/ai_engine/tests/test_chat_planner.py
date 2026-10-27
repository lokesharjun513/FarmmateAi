import pytest

from app.modules.ai_engine.context import AIContext
from app.modules.ai_engine.providers.ai_provider import AIProvider
from app.modules.chat.chat_planner import ChatPlanner


@pytest.fixture
def context():

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


def test_chat_planner_uses_shared_ai_provider():

    planner = ChatPlanner()

    assert isinstance(
        planner.provider,
        AIProvider,
    )


@pytest.mark.asyncio
async def test_chat_planner_returns_stripped_answer(context):

    class MockProvider:

        def __init__(self):

            self.kwargs = None

        async def generate(
            self,
            **kwargs,
        ):

            self.kwargs = kwargs

            return "  Irrigate in the morning.  "

    planner = ChatPlanner()

    provider = MockProvider()

    planner.provider = provider

    answer = await planner.ask(
        context=context,
        history="farmer: How is my crop?",
        question="Should I irrigate today?",
    )

    assert answer == "Irrigate in the morning."

    assert "Should I irrigate today?" in (
        provider.kwargs["user_prompt"]
    )

    assert "farmer: How is my crop?" in (
        provider.kwargs["user_prompt"]
    )

    assert "FarmMate AI" in (
        provider.kwargs["system_prompt"]
    )
