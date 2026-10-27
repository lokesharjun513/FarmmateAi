from datetime import datetime, timedelta, timezone

from app.modules.chat.models import (
    AskFMSession,
    AskFMSessionStatus,
)
from app.modules.chat.session_repository import SessionRepository
from app.modules.farmer.models import Farmer


SESSION_TIMEOUT_MINUTES = 10


class SessionService:

    def __init__(
        self,
        repository: SessionRepository,
    ):
        self.repository = repository

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _expiry_time(
        self,
        current_time: datetime,
    ) -> datetime:
        return current_time + timedelta(
            minutes=SESSION_TIMEOUT_MINUTES,
        )

    def get_or_create_session(
        self,
        farmer: Farmer,
    ) -> AskFMSession:

        session = self.repository.get_active_session(
            farmer.id,
        )

        if session:
            return self.refresh_session(
                session,
            )

        now = self._now()

        new_session = AskFMSession(
            farmer_id=farmer.id,
            status=AskFMSessionStatus.ACTIVE,
            started_at=now,
            last_activity_at=now,
            expires_at=self._expiry_time(
                now,
            ),
        )

        return self.repository.create(
            new_session,
        )

    def refresh_session(
        self,
        session: AskFMSession,
    ) -> AskFMSession:

        now = self._now()

        session.last_activity_at = now
        session.expires_at = self._expiry_time(
            now,
        )

        return self.repository.update(
            session,
        )

    def expire_session(
        self,
        session: AskFMSession,
    ) -> AskFMSession:

        session.status = AskFMSessionStatus.EXPIRED

        return self.repository.update(
            session,
        )