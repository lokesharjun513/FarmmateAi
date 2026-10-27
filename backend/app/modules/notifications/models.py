import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    String,
    Text,
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
# NOTIFICATION TYPE
# ============================================================


class NotificationType(str, Enum):
    """
    Defines the source/category of a notification.
    """

    AI_ADVISOR = "AI_ADVISOR"
    WEATHER = "WEATHER"
    SYSTEM = "SYSTEM"
    GOVERNMENT = "GOVERNMENT"
    DISEASE = "DISEASE"


# ============================================================
# NOTIFICATION PRIORITY
# ============================================================


class NotificationPriority(str, Enum):
    """
    Defines the importance of a notification.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================
# NOTIFICATION
#
# Every notification belongs to exactly one farmer.
#
# Farmer
#    │
#    └── Notifications
#
# When a farmer is deleted, all of their notifications
# are automatically deleted through the database
# foreign-key cascade.
# ============================================================


class Notification(Base, TimestampMixin):

    __tablename__ = "notifications"

    # ========================================================
    # TABLE INDEXES
    # ========================================================

    __table_args__ = (

        # ----------------------------------------------------
        # Latest notifications for a farmer
        # ----------------------------------------------------

        Index(
            "ix_notification_farmer_created",
            "farmer_id",
            "created_at",
        ),

        # ----------------------------------------------------
        # Unread notifications for a farmer
        # ----------------------------------------------------

        Index(
            "ix_notification_farmer_read",
            "farmer_id",
            "is_read",
        ),

        # ----------------------------------------------------
        # Priority-based notification queries
        # ----------------------------------------------------

        Index(
            "ix_notification_farmer_priority",
            "farmer_id",
            "priority",
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
    # FARMER
    #
    # Every notification must belong to a farmer.
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
    # NOTIFICATION TITLE
    # ========================================================

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # ========================================================
    # NOTIFICATION MESSAGE
    # ========================================================

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ========================================================
    # NOTIFICATION TYPE
    # ========================================================

    type: Mapped[NotificationType] = mapped_column(
        SqlEnum(
            NotificationType,
            name="notification_type",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # NOTIFICATION PRIORITY
    #
    # Default:
    #     MEDIUM
    # ========================================================

    priority: Mapped[NotificationPriority] = mapped_column(
        SqlEnum(
            NotificationPriority,
            name="notification_priority",
        ),
        default=NotificationPriority.MEDIUM,
        server_default=NotificationPriority.MEDIUM.value,
        nullable=False,
        index=True,
    )

    # ========================================================
    # READ STATUS
    #
    # False → unread
    # True  → read
    #
    # Default:
    #     False
    # ========================================================

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        index=True,
    )

    # ========================================================
    # FARMER RELATIONSHIP
    #
    # Corresponding relationship must exist in Farmer:
    #
    # notifications = relationship(
    #     "Notification",
    #     back_populates="farmer",
    # )
    # ========================================================

    farmer: Mapped["Farmer"] = relationship(
        "Farmer",
        back_populates="notifications",
    )