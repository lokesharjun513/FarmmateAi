import pytest

from app.modules.ai_engine.orchestrator import AIOrchestrator
from app.shared.exceptions import ValidationError

# ============================================================
# SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_generate_success(monkeypatch):

    expected_response = (
        "Rice crop is healthy. "
        "Check soil moisture today."
    )

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        return expected_response

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    result = await orchestrator.generate(
        system_prompt="You are FarmMate AI.",
        user_prompt="Give advice for rice crop.",
    )

    assert result == expected_response


# ============================================================
# PROVIDER RECEIVES CORRECT PARAMETERS
# ============================================================


@pytest.mark.asyncio
async def test_generate_passes_correct_parameters(
    monkeypatch,
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

        return "AI response"

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    result = await orchestrator.generate(
        system_prompt="SYSTEM PROMPT",
        user_prompt="USER PROMPT",
        temperature=0.7,
        max_tokens=900,
    )

    assert result == "AI response"

    assert captured["system_prompt"] == (
        "SYSTEM PROMPT"
    )

    assert captured["user_prompt"] == (
        "USER PROMPT"
    )

    assert captured["temperature"] == 0.7

    assert captured["max_tokens"] == 900


# ============================================================
# DEFAULT PARAMETERS
# ============================================================


@pytest.mark.asyncio
async def test_generate_uses_default_parameters(
    monkeypatch,
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

        captured["temperature"] = temperature
        captured["max_tokens"] = max_tokens

        return "AI response"

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    result = await orchestrator.generate(
        system_prompt="SYSTEM",
        user_prompt="USER",
    )

    assert result == "AI response"

    assert captured["temperature"] == 0.2

    assert captured["max_tokens"] == 500


# ============================================================
# CUSTOM TEMPERATURE
# ============================================================


@pytest.mark.asyncio
async def test_generate_supports_custom_temperature(
    monkeypatch,
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

        captured["temperature"] = temperature

        return "AI response"

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    await orchestrator.generate(
        system_prompt="SYSTEM",
        user_prompt="USER",
        temperature=0.0,
    )

    assert captured["temperature"] == 0.0


# ============================================================
# CUSTOM MAX TOKENS
# ============================================================


@pytest.mark.asyncio
async def test_generate_supports_custom_max_tokens(
    monkeypatch,
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

        captured["max_tokens"] = max_tokens

        return "AI response"

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    await orchestrator.generate(
        system_prompt="SYSTEM",
        user_prompt="USER",
        max_tokens=1500,
    )

    assert captured["max_tokens"] == 1500


# ============================================================
# PROVIDER ERROR
# ============================================================


@pytest.mark.asyncio
async def test_generate_provider_error_becomes_validation_error(
    monkeypatch,
):

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        raise RuntimeError(
            "AI connection failed"
        )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    with pytest.raises(
        ValidationError,
        match=(
            "Unable to generate AI response at the moment. "
            "Please try again."
        ),
    ):

        await orchestrator.generate(
            system_prompt="SYSTEM",
            user_prompt="USER",
        )


# ============================================================
# PROVIDER VALUE ERROR
# ============================================================


@pytest.mark.asyncio
async def test_generate_provider_value_error_becomes_validation_error(
    monkeypatch,
):

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        raise ValueError(
            "Invalid provider configuration"
        )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    with pytest.raises(
        ValidationError,
        match=(
            "Unable to generate AI response at the moment. "
            "Please try again."
        ),
    ):

        await orchestrator.generate(
            system_prompt="SYSTEM",
            user_prompt="USER",
        )


# ============================================================
# PROVIDER RESPONSE IS RETURNED UNCHANGED
# ============================================================


@pytest.mark.asyncio
async def test_generate_returns_provider_response_unchanged(
    monkeypatch,
):

    provider_response = (
        '  {"summary": "Rice is healthy."}  '
    )

    async def mock_generate(
        self,
        *,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ):

        return provider_response

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.AIProvider.generate",
        mock_generate,
    )

    orchestrator = AIOrchestrator()

    result = await orchestrator.generate(
        system_prompt="SYSTEM",
        user_prompt="USER",
    )

    assert result == provider_response