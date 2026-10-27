from app.modules.ai_engine.providers.ai_provider import (
    AIProvider,
)
from app.shared.exceptions import ValidationError


class AIOrchestrator:

    def __init__(self):
        self.provider = AIProvider()

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 500,
    ) -> str:

        try:

            return await self.provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except Exception as exc:

            raise ValidationError(
                "Unable to generate AI response at the moment. Please try again."
            ) from exc