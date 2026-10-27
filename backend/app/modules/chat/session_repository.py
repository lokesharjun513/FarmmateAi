from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.chat.models import (
    AskFMSession,
    AskFMSessionStatus,
)


class SessionRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_by_id(
        self,
        session_id: UUID,
    ) -> AskFMSession | None:

        return (
            self.db.query(AskFMSession)
            .filter(
                AskFMSession.id == session_id,
            )
            .first()
        )

    def get_by_id_and_farmer(
        self,
        session_id: UUID,
        farmer_id: UUID,
    ) -> AskFMSession | None:

        return (
            self.db.query(AskFMSession)
            .filter(
                AskFMSession.id == session_id,
                AskFMSession.farmer_id == farmer_id,
            )
            .first()
        )

    def get_active_session(
        self,
        farmer_id: UUID,
    ) -> AskFMSession | None:

        return (
            self.db.query(AskFMSession)
            .filter(
                AskFMSession.farmer_id == farmer_id,
                AskFMSession.status == AskFMSessionStatus.ACTIVE,
                AskFMSession.expires_at > datetime.now(
                    timezone.utc,
                ),
            )
            .order_by(
                AskFMSession.last_activity_at.desc(),
            )
            .first()
        )

    def get_all_by_farmer(
        self,
        farmer_id: UUID,
    ) -> list[AskFMSession]:

        return (
            self.db.query(AskFMSession)
            .filter(
                AskFMSession.farmer_id == farmer_id,
            )
            .order_by(
                AskFMSession.last_activity_at.desc(),
            )
            .all()
        )

    def create(
        self,
        session: AskFMSession,
    ) -> AskFMSession:

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def update(
        self,
        session: AskFMSession,
    ) -> AskFMSession:

        self.db.commit()
        self.db.refresh(session)

        return session

    def expire(
        self,
        session: AskFMSession,
    ) -> AskFMSession:

        session.status = AskFMSessionStatus.EXPIRED

        return self.update(session)

    def delete(
        self,
        session: AskFMSession,
    ) -> None:

        self.db.delete(session)
        self.db.commit()

    def get_expired_sessions(
        self,
        now: datetime,
    ) -> list[AskFMSession]:

        return (
            self.db.query(AskFMSession)
            .filter(
                AskFMSession.status == AskFMSessionStatus.ACTIVE,
                AskFMSession.expires_at <= now,
            )
            .all()
        )

    def delete_expired_sessions(
        self,
        now: datetime,
    ) -> int:

        count = (
            self.db.query(AskFMSession)
            .filter(
                AskFMSession.status == AskFMSessionStatus.EXPIRED,
                AskFMSession.expires_at <= now,
            )
            .delete(
                synchronize_session=False,
            )
        )

        self.db.commit()

        return count