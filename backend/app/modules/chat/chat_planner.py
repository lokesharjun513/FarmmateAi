from app.modules.ai_engine.context import AIContext
from app.modules.ai_engine.providers.ai_provider import AIProvider
from app.modules.chat.prompts import (
    chat_system_prompt,
    chat_user_prompt,
)


class ChatPlanner:

    def __init__(self):
        self.provider = AIProvider()

    async def ask(
        self,
        *,
        context: AIContext,
        history: str,
        question: str,
        language: str = "English",
    ) -> str:
        """
        Generate AI response using
        FarmMate chat context.
        """

        system_prompt = chat_system_prompt()

        user_prompt = chat_user_prompt(
            context=context,
            history=history,
            question=question,
            language=language,
        )

        response = await self.provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return response.strip()