from datetime import datetime, timezone

from app.modules.chat.session_repository import SessionRepository
from app.modules.chat.message_repository import MessageRepository


class SessionCleanupService:

    def __init__(
        self,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
    ):
        self.session_repository = session_repository
        self.message_repository = message_repository

    def cleanup(self) -> None:

        expired_sessions = (
            self.session_repository.get_expired_sessions(
                datetime.now(timezone.utc),
            )
        )

        for session in expired_sessions:

            self.message_repository.delete_session_messages(
                session.id,
            )

            self.session_repository.delete(
                session,
            )