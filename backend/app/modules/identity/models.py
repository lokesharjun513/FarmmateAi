import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

    from app.modules.farmer.models import Farmer


# ============================================================
# USER
#
# Represents the authentication identity of a user.
#
# User
#   ↓
# Farmer Profile
#
# One user can have at most one farmer profile.
#
# Authentication-related information belongs here:
#
# - Name
# - Mobile
# - Email
# - Password hash
# - Account status
#
# Farming-specific information belongs to Farmer.
# ============================================================


class User(Base, TimestampMixin):

    __tablename__ = "users"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ========================================================
    # BASIC INFORMATION
    # ========================================================

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ========================================================
    # MOBILE
    #
    # Used as a unique identity/contact field.
    #
    # The unique constraint ensures that two users cannot
    # register using the same mobile number.
    # ========================================================

    mobile: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    # ========================================================
    # EMAIL
    #
    # Email is unique so two users cannot register using
    # the same email address.
    # ========================================================

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # ========================================================
    # PASSWORD
    #
    # IMPORTANT:
    #
    # Never store the plain-text password.
    #
    # This column stores only the password hash.
    # ========================================================

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ========================================================
    # ACCOUNT STATUS
    #
    # True:
    #     User can authenticate.
    #
    # False:
    #     User account is disabled.
    #
    # This is also checked by get_current_user().
    # ========================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # ========================================================
    # FARMER PROFILE
    #
    # One User
    #     ↓
    # Zero or One Farmer
    #
    # Farmer contains farming-specific information.
    #
    # User
    #   ├── full_name
    #   ├── mobile
    #   ├── email
    #   └── password_hash
    #
    # Farmer
    #   ├── preferred_language
    #   ├── experience_years
    #   ├── profile_completion
    #   └── onboarding information
    #
    # ========================================================

    farmer: Mapped["Farmer | None"] = relationship(
        "Farmer",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )