from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base
from app.shared.mixins import TimestampMixin


if TYPE_CHECKING:

    from app.modules.farmer.models import Farmer


# ============================================================
# ASK FM SESSION STATUS
# ============================================================


class AskFMSessionStatus(str, enum.Enum):

    ACTIVE = "ACTIVE"

    EXPIRED = "EXPIRED"


# ============================================================
# ASK FM MESSAGE ROLE
# ============================================================


class AskFMRole(str, enum.Enum):

    USER = "USER"

    ASSISTANT = "ASSISTANT"

    SYSTEM = "SYSTEM"


# ============================================================
# ASK FM SESSION
#
# Represents one conversational session between a farmer
# and the Ask FM AI assistant.
#
# Farmer
#    │
#    └── AskFMSession
#           │
#           └── AskFMMessage
#                 ├── USER
#                 ├── ASSISTANT
#                 └── SYSTEM
#
# A session belongs to exactly one farmer.
# A session can contain many messages.
# ============================================================


class AskFMSession(Base, TimestampMixin):

    __tablename__ = "ask_fm_sessions"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ========================================================
    # FARMER
    #
    # Every Ask FM session belongs to exactly one farmer.
    #
    # If the farmer is deleted, the session is deleted.
    # ========================================================

    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farmers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # SESSION STATUS
    # ========================================================

    status: Mapped[AskFMSessionStatus] = mapped_column(
        Enum(
            AskFMSessionStatus,
            name="ask_fm_session_status",
        ),
        default=AskFMSessionStatus.ACTIVE,
        nullable=False,
    )

    # ========================================================
    # SESSION TIMELINE
    # ========================================================

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ========================================================
    # FARMER RELATIONSHIP
    # ========================================================

    farmer: Mapped["Farmer"] = relationship(
        "Farmer",
        back_populates="ask_fm_sessions",
    )

    # ========================================================
    # MESSAGES
    #
    # Messages are ordered using message_order.
    #
    # This is intentionally NOT based only on created_at,
    # because multiple messages can have the same timestamp.
    # ========================================================

    messages: Mapped[list["AskFMMessage"]] = relationship(
        "AskFMMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AskFMMessage.message_order",
        lazy="selectin",
    )


# ============================================================
# ASK FM MESSAGE
#
# Represents one message inside an Ask FM session.
#
# Example:
#
# USER:
#     "What fertilizer should I use?"
#
# ASSISTANT:
#     "For your rice crop..."
#
# SYSTEM:
#     Internal system message.
# ============================================================


class AskFMMessage(Base, TimestampMixin):

    __tablename__ = "ask_fm_messages"

    # ========================================================
    # TABLE CONSTRAINTS
    # ========================================================
    #
    # Every message inside a session must have a unique
    # sequential order number.
    #
    # Example:
    #
    # session A:
    #   1 USER
    #   2 ASSISTANT
    #   3 USER
    #   4 ASSISTANT
    #
    # session B:
    #   1 USER
    #   2 ASSISTANT
    #
    # ========================================================

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "message_order",
            name="uq_ask_fm_message_session_order",
        ),
    )

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ========================================================
    # SESSION
    #
    # Every message belongs to exactly one session.
    #
    # If the session is deleted, all messages are deleted.
    # ========================================================

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ask_fm_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # MESSAGE ORDER
    #
    # Determines the exact chronological position of a
    # message inside a conversation.
    #
    # IMPORTANT:
    #
    # Do NOT use created_at as the only ordering mechanism.
    #
    # created_at can be identical for multiple messages,
    # especially when several messages are inserted quickly.
    #
    # The repository is responsible for assigning this value.
    # ========================================================

    message_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # MESSAGE ROLE
    # ========================================================

    role: Mapped[AskFMRole] = mapped_column(
        Enum(
            AskFMRole,
            name="ask_fm_role",
        ),
        nullable=False,
    )

    # ========================================================
    # MESSAGE CONTENT
    # ========================================================

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ========================================================
    # SESSION RELATIONSHIP
    # ========================================================

    session: Mapped["AskFMSession"] = relationship(
        "AskFMSession",
        back_populates="messages",
    )