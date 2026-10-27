from app.modules.activity.repository import ActivityRepository
from app.modules.ai_engine.context_builder import AIContextBuilder
from app.modules.ai_engine.providers.ai_provider import AIProviderError
from app.modules.chat.chat_planner import ChatPlanner
from app.modules.chat.message_repository import MessageRepository
from app.modules.chat.session_repository import SessionRepository
from app.modules.chat.session_service import SessionService
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.models import Farmer
from app.modules.weather.service import WeatherService

MAX_HISTORY_MESSAGES = 20


class ChatService:

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        crop_repository: CropSeasonRepository,
        activity_repository: ActivityRepository,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
        weather_service: WeatherService,
    ):
        self.context_builder = AIContextBuilder(
            farm_repository=farm_repository,
            crop_repository=crop_repository,
            activity_repository=activity_repository,
            weather_service=weather_service,
        )

        self.session_service = SessionService(
            repository=session_repository,
        )

        self.message_repository = message_repository

        self.planner = ChatPlanner()

    async def chat(
        self,
        *,
        current_farmer: Farmer,
        message: str,
    ) -> str:
        """
        Complete Ask FM workflow.

        1. Get/Create session
        2. Load previous conversation
        3. Save farmer message
        4. Build farm context
        5. Ask AI
        6. Save AI response
        7. Refresh session timeout
        """

        message = message.strip()

        if not message:
            raise ValueError(
                "Message cannot be empty."
            )

        session = self.session_service.get_or_create_session(
            current_farmer,
        )

        chat_messages = self.message_repository.get_recent_messages(
            session.id,
            limit=MAX_HISTORY_MESSAGES,
        )

        history = "\n".join(
            f"{chat_message.role.value}: {chat_message.content}"
            for chat_message in chat_messages
        )

        try:
            context = await self.context_builder.build(
                current_farmer,
            )

            answer = await self.planner.ask(
                context=context,
                history=history,
                question=message,
            )

            if not answer:
                raise AIProviderError(
                    "AI returned an empty response."
                )

            self.message_repository.create_user_message(
                session_id=session.id,
                content=message,
            )
            self.message_repository.create_assistant_message(
                session_id=session.id,
                content=answer,
            )

            return answer

        finally:
            self.session_service.refresh_session(
                session,
            )