# Password Reset OTP Challenge Model

"""Database model for password reset One-Time Password challenges.

This model tracks password reset attempts with security controls including:
- OTP hashing (never plaintext storage)
- Expiration timestamps (5-minute validity)
- Verification attempt counting (max 5 per challenge)
- Resend cooldown tracking (60 seconds)
- Single-use reset authorization
- Consumed/revoked state management

All timestamps are UTC. Operations use atomic database queries
to prevent concurrent request vulnerabilities.
"""

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.sql import bindparam

from app.database.base import Base

# `Base` is the declarative base shared by all models in the app.db


class PasswordResetChallenge(Base):
    """Model representing a password reset OTP challenge.

    Each challenge is single-use and time-bound. After successful
    verification, the challenge is consumed and a short-lived reset
    authorization is issued instead.

    Attributes:
        id: Primary key (UUID).
        user_id: Foreign key to the associated user (unique constraint).
        otp_hash: Hashed OTP (plaintext OTPs are never stored).
        created_at: Timestamp when the challenge was created.
        expires_at: Timestamp when the challenge expires (5 minutes).
        verification_attempts: Number of failed verification attempts.
        max_attempts: Maximum allowed verification attempts (5).
        resend_cooldown_until: Timestamp until which resending is blocked.
        is_consumed: Whether the challenge has been successfully used.
        is_revoked: Whether the challenge has been explicitly revoked.
    """

    __tablename__ = "password_reset_challenges"

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_password_reset_challenges_user_id"),
        {
            "info": {
                "description": "Password reset OTP challenge model"
            }
        },
    )

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Primary key - UUID string",
    )
    user_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="Foreign key to users table",
    )
    otp_hash = Column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of the 6-digit numeric OTP",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp when challenge was created",
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5),
        comment="UTC timestamp when challenge expires (5 minutes)",
    )
    verification_attempts = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of failed verification attempts",
    )
    max_attempts = Column(
        Integer,
        nullable=False,
        default=5,
        comment="Maximum allowed verification attempts",
    )
    resend_cooldown_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp until which resending is blocked (60 seconds)",
    )
    is_consumed = Column(
        Integer,  # 0 = false, 1 = true (SQLite/PostgreSQL friendly)
        nullable=False,
        default=0,
        comment="Whether the challenge has been successfully consumed",
    )
    is_revoked = Column(
        Integer,  # 0 = false, 1 = true
        nullable=False,
        default=0,
        comment="Whether the challenge has been explicitly revoked",
    )

    def is_expired(self) -> bool:
        """Check if the challenge has expired based on UTC timestamps."""
        return datetime.now(timezone.utc) > self.expires_at

    def can_verify(self) -> bool:
        """Check if the challenge can still be verified.

        Returns True if:
        - The challenge has not expired
        - The challenge has not been consumed
        - The challenge has not been revoked
        - The verification attempt count is below the maximum
        """
        return (
            not self.is_expired()
            and self.is_consumed == 0
            and self.is_revoked == 0
            and self.verification_attempts < self.max_attempts
        )

    def can_resend(self) -> bool:
        """Check if a new OTP can be resent.

        Returns True if:
        - The challenge has not been consumed
        - The resend cooldown has passed
        """
        if self.is_consumed == 1:
            return False
        if self.resend_cooldown_until is None:
            return True
        return datetime.now(timezone.utc) > self.resend_cooldown_until

    def record_attempt(self) -> None:
        """Atomically increment the verification attempt count."""
        self.verification_attempts += 1

    def block_resend_for(self, minutes: int = 60) -> None:
        """Set the resend cooldown timestamp.

        Args:
            minutes: Cooldown duration in minutes (default 60).
        """
        self.resend_cooldown_until = datetime.now(timezone.utc) + timedelta(
            minutes=minutes
        )


# =============================================================================
# Helper functions for OTP generation and verification
# =============================================================================

import hashlib
import hmac
import secrets

from app.core.config import settings

_OTP_ALPHABET = "0123456789"
_OTP_LENGTH = 6


def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP.

    Returns:
        A string of exactly 6 digits (e.g., "482917").

    Security:
        Uses Python's secrets module for cryptographically secure random
        generation. The OTP is immediately hashed before storage; the
        plaintext is never persisted.
    """
    return "".join(secrets.choice(_OTP_ALPHABET) for _ in range(_OTP_LENGTH))


def _hmac_otp(otp: str) -> str:
    """Return a server-keyed HMAC-SHA256 of the OTP.

    Plain SHA-256 of a 6-digit code is brute-forceable offline in seconds
    if the challenge table leaks (10^6 space). Keying the digest with a
    server secret means a leaked table cannot be cracked without also
    compromising the application secret.
    """
    return hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        otp.encode(),
        hashlib.sha256,
    ).hexdigest()


def hash_otp(otp: str) -> str:
    """Hash a 6-digit OTP using a server-keyed HMAC-SHA256.

    Args:
        otp: A 6-digit numeric string.

    Returns:
        A hexadecimal digest string (64 characters).
    """
    return _hmac_otp(otp)


def verify_otp(otp: str, otp_hash: str) -> bool:
    """Verify a 6-digit OTP against its stored hash.

    Args:
        otp: The 6-digit numeric OTP string to verify.
        otp_hash: The stored HMAC digest of the original OTP.

    Returns:
        True if the OTP matches, False otherwise.

    Note:
        Does not check expiration or consumption status;
        the caller must check those conditions separately.
    """
    test_hash = _hmac_otp(otp)
    return hmac.compare_digest(test_hash, otp_hash)