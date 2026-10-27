from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.chat.models import (
    AskFMMessage,
    AskFMRole,
)


DEFAULT_HISTORY_LIMIT = 20


class MessageRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        message: AskFMMessage,
    ) -> AskFMMessage:

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message

    # ========================================================
    # MESSAGE ORDER
    # ========================================================

    def _get_next_message_order(
        self,
        session_id: UUID,
    ) -> int:

        last_order = (
            self.db.query(
                func.max(
                    AskFMMessage.message_order,
                )
            )
            .filter(
                AskFMMessage.session_id == session_id,
            )
            .scalar()
        )

        return (last_order or 0) + 1

    # ========================================================
    # USER MESSAGE
    # ========================================================

    def create_user_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> AskFMMessage:

        message_order = self._get_next_message_order(
            session_id,
        )

        return self.create(
            AskFMMessage(
                session_id=session_id,
                message_order=message_order,
                role=AskFMRole.USER,
                content=content,
            )
        )

    # ========================================================
    # ASSISTANT MESSAGE
    # ========================================================

    def create_assistant_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> AskFMMessage:

        message_order = self._get_next_message_order(
            session_id,
        )

        return self.create(
            AskFMMessage(
                session_id=session_id,
                message_order=message_order,
                role=AskFMRole.ASSISTANT,
                content=content,
            )
        )

    # ========================================================
    # SYSTEM MESSAGE
    # ========================================================

    def create_system_message(
        self,
        *,
        session_id: UUID,
        content: str,
    ) -> AskFMMessage:

        message_order = self._get_next_message_order(
            session_id,
        )

        return self.create(
            AskFMMessage(
                session_id=session_id,
                message_order=message_order,
                role=AskFMRole.SYSTEM,
                content=content,
            )
        )

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        message_id: UUID,
    ) -> AskFMMessage | None:

        return (
            self.db.query(AskFMMessage)
            .filter(
                AskFMMessage.id == message_id,
            )
            .first()
        )

    # ========================================================
    # GET ALL MESSAGES
    #
    # Always return messages in conversation order.
    # ========================================================

    def get_messages(
        self,
        session_id: UUID,
    ) -> list[AskFMMessage]:

        return (
            self.db.query(AskFMMessage)
            .filter(
                AskFMMessage.session_id == session_id,
            )
            .order_by(
                AskFMMessage.message_order.asc(),
            )
            .all()
        )

    # ========================================================
    # GET RECENT MESSAGES
    #
    # Example:
    #
    # Orders:
    # 1  2  3  4  5  6  7  8  9  10
    #
    # limit=5
    #
    # Returns:
    # 6  7  8  9  10
    #
    # But returned to caller in chronological order.
    # ========================================================

    def get_recent_messages(
        self,
        session_id: UUID,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> list[AskFMMessage]:

        messages = (
            self.db.query(AskFMMessage)
            .filter(
                AskFMMessage.session_id == session_id,
            )
            .order_by(
                AskFMMessage.message_order.desc(),
            )
            .limit(limit)
            .all()
        )

        return list(
            reversed(messages)
        )

    # ========================================================
    # DELETE SESSION MESSAGES
    # ========================================================

    def delete_session_messages(
        self,
        session_id: UUID,
    ) -> int:

        deleted = (
            self.db.query(AskFMMessage)
            .filter(
                AskFMMessage.session_id == session_id,
            )
            .delete(
                synchronize_session=False,
            )
        )

        self.db.commit()

        return deleted