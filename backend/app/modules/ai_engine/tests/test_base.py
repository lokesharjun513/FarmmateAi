import pytest

from app.modules.ai_engine.providers.base import (
    BaseAIProvider,
)


# ============================================================
# CONCRETE TEST PROVIDER
# ============================================================


class TestProvider(BaseAIProvider):

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:

        return "test response"


# ============================================================
# ABSTRACT CLASS
# ============================================================


def test_base_provider_cannot_be_instantiated():

    with pytest.raises(
        TypeError,
    ):

        BaseAIProvider()


# ============================================================
# CONCRETE IMPLEMENTATION
# ============================================================


def test_concrete_provider_can_be_instantiated():

    provider = TestProvider()

    assert isinstance(
        provider,
        BaseAIProvider,
    )


# ============================================================
# GENERATE
# ============================================================


@pytest.mark.asyncio
async def test_concrete_provider_generate():

    provider = TestProvider()

    result = await provider.generate(
        system_prompt="System prompt",
        user_prompt="User prompt",
    )

    assert result == "test response"


# ============================================================
# OPTIONAL PARAMETERS
# ============================================================


@pytest.mark.asyncio
async def test_concrete_provider_generate_accepts_optional_parameters():

    provider = TestProvider()

    result = await provider.generate(
        system_prompt="System prompt",
        user_prompt="User prompt",
        temperature=0.5,
        max_tokens=1000,
    )

    assert result == "test response"


# ============================================================
# ABSTRACT METHOD CONTRACT
# ============================================================


def test_generate_is_abstract():

    assert getattr(
        BaseAIProvider.generate,
        "__isabstractmethod__",
        False,
    ) is True