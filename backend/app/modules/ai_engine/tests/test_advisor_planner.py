import pytest

from app.modules.advisor.schemas import (
    AdvicePriority,
    DailyAdvisorResponse,
)

from app.modules.ai_engine.advisor_planner import (
    AdvisorPlanner,
)

from app.modules.ai_engine.context import (
    AIContext,
)

from app.modules.ai_engine.orchestrator import (
    AIOrchestrator,
)

from app.modules.ai_engine.parser import (
    AIResponseParser,
)


# ============================================================
# TEST CONTEXT
# ============================================================


@pytest.fixture
def ai_context():

    return AIContext(
        crop_name="Rice",
        crop_variety="BPT 5204",
        crop_age_days=45,
        soil_type="Clay",
        location="Nellore, Andhra Pradesh",
        weather="Partly Cloudy",
        temperature=31.5,
        humidity=72,
        rain_probability=30,
        today_activities=[
            "Irrigate field",
            "Inspect crop for pests",
        ],
    )


# ============================================================
# MOCK RESPONSE
# ============================================================


@pytest.fixture
def mock_advice():

    return DailyAdvisorResponse(
        summary=(
            "Rice crop is growing well. "
            "Monitor soil moisture before irrigation."
        ),
        warnings=[
            "Moderate rain probability may affect irrigation."
        ],
        recommendations=[
            "Check soil moisture before irrigation.",
            "Inspect leaves for pest damage.",
            "Avoid unnecessary pesticide spraying.",
        ],
        priority=AdvicePriority.MEDIUM,
    )


# ============================================================
# SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_generate_daily_advice_success(
    monkeypatch,
    ai_context,
    mock_advice,
):

    generated_response = """
    {
        "summary": "Rice crop is growing well.",
        "warnings": [
            "Moderate rain probability."
        ],
        "recommendations": [
            "Check soil moisture.",
            "Inspect the crop."
        ],
        "priority": "MEDIUM"
    }
    """

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        return generated_response

    monkeypatch.setattr(
        AIOrchestrator,
        "generate",
        mock_generate,
    )

    def mock_parse_daily_advice(
        response,
    ):

        assert response == generated_response

        return mock_advice

    monkeypatch.setattr(
        AIResponseParser,
        "parse_daily_advice",
        mock_parse_daily_advice,
    )

    planner = AdvisorPlanner()

    result = await planner.generate_daily_advice(
        context=ai_context,
    )

    assert result == mock_advice

    assert result.priority == AdvicePriority.MEDIUM
    assert result.summary.startswith("Rice crop")


# ============================================================
# ORCHESTRATOR PARAMETERS
# ============================================================


@pytest.mark.asyncio
async def test_orchestrator_receives_correct_parameters(
    monkeypatch,
    ai_context,
):

    captured = {}

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        captured["temperature"] = temperature
        captured["max_tokens"] = max_tokens

        return "mock response"

    monkeypatch.setattr(
        AIOrchestrator,
        "generate",
        mock_generate,
    )

    def mock_parse_daily_advice(
        response,
    ):

        return DailyAdvisorResponse(
            summary="Test summary",
            warnings=[],
            recommendations=[
                "Test recommendation",
            ],
            priority=AdvicePriority.LOW,
        )

    monkeypatch.setattr(
        AIResponseParser,
        "parse_daily_advice",
        mock_parse_daily_advice,
    )

    planner = AdvisorPlanner()

    await planner.generate_daily_advice(
        context=ai_context,
    )

    assert captured["temperature"] == 0.2
    assert captured["max_tokens"] == 1000

    assert captured["system_prompt"]
    assert captured["user_prompt"]


# ============================================================
# USER PROMPT CONTAINS CONTEXT
# ============================================================


@pytest.mark.asyncio
async def test_user_prompt_contains_context(
    monkeypatch,
    ai_context,
):

    captured = {}

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt

        return "mock response"

    monkeypatch.setattr(
        AIOrchestrator,
        "generate",
        mock_generate,
    )

    monkeypatch.setattr(
        AIResponseParser,
        "parse_daily_advice",
        lambda response: DailyAdvisorResponse(
            summary="Test",
            warnings=[],
            recommendations=["Test"],
            priority=AdvicePriority.LOW,
        ),
    )

    planner = AdvisorPlanner()

    await planner.generate_daily_advice(
        context=ai_context,
    )

    user_prompt = captured["user_prompt"]

    assert "Rice" in user_prompt
    assert "BPT 5204" in user_prompt
    assert "45 days" in user_prompt
    assert "Clay" in user_prompt
    assert "Nellore, Andhra Pradesh" in user_prompt
    assert "Partly Cloudy" in user_prompt
    assert "31.5" in user_prompt
    assert "72%" in user_prompt
    assert "30%" in user_prompt
    assert "Irrigate field" in user_prompt
    assert "Inspect crop for pests" in user_prompt


# ============================================================
# SYSTEM PROMPT IS GENERATED
# ============================================================


@pytest.mark.asyncio
async def test_system_prompt_is_generated(
    monkeypatch,
    ai_context,
):

    captured = {}

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        captured["system_prompt"] = system_prompt

        return "mock response"

    monkeypatch.setattr(
        AIOrchestrator,
        "generate",
        mock_generate,
    )

    monkeypatch.setattr(
        AIResponseParser,
        "parse_daily_advice",
        lambda response: DailyAdvisorResponse(
            summary="Test",
            warnings=[],
            recommendations=["Test"],
            priority=AdvicePriority.LOW,
        ),
    )

    planner = AdvisorPlanner()

    await planner.generate_daily_advice(
        context=ai_context,
    )

    system_prompt = captured["system_prompt"]

    assert system_prompt
    assert "FarmMate AI" in system_prompt
    assert "agricultural" in system_prompt.lower()


# ============================================================
# PARSER IS CALLED
# ============================================================


@pytest.mark.asyncio
async def test_parser_receives_orchestrator_response(
    monkeypatch,
    ai_context,
):

    ai_response = "AI GENERATED RESPONSE"

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        return ai_response

    monkeypatch.setattr(
        AIOrchestrator,
        "generate",
        mock_generate,
    )

    captured = {}

    def mock_parse_daily_advice(
        response,
    ):

        captured["response"] = response

        return DailyAdvisorResponse(
            summary="Parsed advice",
            warnings=[],
            recommendations=[
                "Parsed recommendation",
            ],
            priority=AdvicePriority.HIGH,
        )

    monkeypatch.setattr(
        AIResponseParser,
        "parse_daily_advice",
        mock_parse_daily_advice,
    )

    planner = AdvisorPlanner()

    result = await planner.generate_daily_advice(
        context=ai_context,
    )

    assert captured["response"] == ai_response

    assert result.summary == "Parsed advice"
    assert result.priority == AdvicePriority.HIGH


# ============================================================
# DIFFERENT PRIORITIES
# ============================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "priority",
    [
        AdvicePriority.LOW,
        AdvicePriority.MEDIUM,
        AdvicePriority.HIGH,
    ],
)
async def test_generate_daily_advice_supports_all_priorities(
    monkeypatch,
    ai_context,
    priority,
):

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        return "mock response"

    monkeypatch.setattr(
        AIOrchestrator,
        "generate",
        mock_generate,
    )

    monkeypatch.setattr(
        AIResponseParser,
        "parse_daily_advice",
        lambda response: DailyAdvisorResponse(
            summary="Test summary",
            warnings=[],
            recommendations=["Test recommendation"],
            priority=priority,
        ),
    )

    planner = AdvisorPlanner()

    result = await planner.generate_daily_advice(
        context=ai_context,
    )

    assert result.priority == priority