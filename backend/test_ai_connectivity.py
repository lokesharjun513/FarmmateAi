import asyncio
from app.core.config import settings
from app.modules.ai_engine.providers.ai_provider import AIProvider

async def test_ai():
    provider = AIProvider()
    print(f"Testing with URL: {settings.AI_API_URL}")
    print(f"Testing with Model: {settings.AI_MODEL}")
    try:
        response = await provider.generate(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello, are you working?",
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai())
