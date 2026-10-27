import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
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

    from app.modules.identity.models import User
    from app.modules.farm.models import Farm
    from app.modules.notifications.models import Notification
    from app.modules.notifications.models_device import DeviceToken
    from app.modules.chat.models import AskFMSession


# ============================================================
# FARMER
#
# Represents the farming profile of an authenticated user.
#
# User
#   ↓
# Farmer
#   ├── Farms
#   ├── Notifications
#   └── Ask FM Sessions
#
# Authentication information belongs to User.
# Farming/profile information belongs to Farmer.
# ============================================================


class Farmer(Base, TimestampMixin):

    __tablename__ = "farmers"

    # ========================================================
    # TABLE CONSTRAINTS
    # ========================================================

    __table_args__ = (

        # ----------------------------------------------------
        # Profile completion must remain between 0 and 100.
        # ----------------------------------------------------

        CheckConstraint(
            "profile_completion >= 0 "
            "AND profile_completion <= 100",
            name="ck_farmer_profile_completion_valid",
        ),

        # ----------------------------------------------------
        # Experience years cannot be negative.
        # ----------------------------------------------------

        CheckConstraint(
            "experience_years IS NULL "
            "OR experience_years >= 0",
            name="ck_farmer_experience_years_valid",
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
    # USER
    #
    # One User → One Farmer
    #
    # unique=True guarantees the one-to-one relationship at
    # the database level.
    # ========================================================

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )

    # ========================================================
    # PREFERRED LANGUAGE
    #
    # Used by the mobile application and AI responses.
    #
    # Example:
    #
    # English
    # Telugu
    # Hindi
    # ========================================================

    preferred_language: Mapped[str] = mapped_column(
        String(20),
        default="English",
        nullable=False,
    )

    # ========================================================
    # FARMING EXPERIENCE
    #
    # NULL is allowed because the farmer may not have
    # provided this information during onboarding.
    # ========================================================

    experience_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ========================================================
    # PROFILE COMPLETION
    #
    # Percentage:
    #
    # 0   → Empty profile
    # 50  → Partially completed
    # 100 → Fully completed
    # ========================================================

    profile_completion: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ========================================================
    # ONBOARDING STATUS
    #
    # False → Farmer has not completed onboarding.
    # True  → Farmer has completed onboarding.
    # ========================================================

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # ========================================================
    # USER RELATIONSHIP
    #
    # Farmer → User
    #
    # One farmer belongs to exactly one user.
    # ========================================================

    user: Mapped["User"] = relationship(
        "User",
        back_populates="farmer",
    )

    # ========================================================
    # FARMS
    #
    # One farmer can own multiple farms.
    #
    # Farmer
    #   ├── Farm 1
    #   ├── Farm 2
    #   └── Farm 3
    #
    # Deleting a farmer deletes their farms.
    # ========================================================

    farms: Mapped[list["Farm"]] = relationship(
        "Farm",
        back_populates="farmer",
        cascade="all, delete-orphan",
    )

    # ========================================================
    # NOTIFICATIONS
    #
    # One farmer can have many notifications.
    #
    # Deleting a farmer deletes their notifications.
    # ========================================================

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="farmer",
        cascade="all, delete-orphan",
    )

    device_tokens: Mapped[list["DeviceToken"]] = relationship(
        "DeviceToken",
        back_populates="farmer",
        cascade="all, delete-orphan",
    )

    # ========================================================
    # ASK FM SESSIONS
    #
    # One farmer can have many AI conversation sessions.
    #
    # Farmer
    #   ├── Session 1
    #   │     ├── Message
    #   │     └── Message
    #   │
    #   ├── Session 2
    #   │     └── Message
    #   │
    #   └── Session 3
    #
    # Deleting a farmer deletes their Ask FM sessions.
    # The sessions then cascade-delete their messages.
    # ========================================================

    ask_fm_sessions: Mapped[list["AskFMSession"]] = relationship(
        "AskFMSession",
        back_populates="farmer",
        cascade="all, delete-orphan",
    )