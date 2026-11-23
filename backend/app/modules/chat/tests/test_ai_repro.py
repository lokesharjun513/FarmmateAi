import asyncio
import pytest
from app.core.config import settings
from app.modules.ai_engine.providers.ai_provider import AIProvider, AIProviderError

@pytest.mark.asyncio
async def test_ai_provider_call():
    provider = AIProvider()
    print(f"Testing with URL: {settings.AI_API_URL}")
    print(f"Testing with Model: {settings.AI_MODEL}")

    try:
        response = await provider.generate(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello",
        )
        print(f"Response: {response}")
    except AIProviderError as e:
        print(f"Caught AIProviderError: {e}")
        pytest.fail(f"AIProviderError: {e}")
    except Exception as e:
        print(f"Caught unexpected Exception: {e}")
        pytest.fail(f"Unexpected Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_provider_call())
