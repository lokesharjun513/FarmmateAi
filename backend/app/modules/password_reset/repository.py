# Password Reset Challenge Repository

"""Repository layer for password reset challenge operations.

Provides atomic database operations for managing password reset challenges
with security controls including rate limiting, cooldown enforcement,
concurrent request safety, and single-use guarantee.

All operations use atomic SQLAlchemy constructs to prevent race conditions
where concurrent requests could otherwise consume or invalidate the same
challenge more than once.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.modules.password_reset.models import PasswordResetChallenge, hash_otp

RESEND_COOLDOWN_SECONDS = 60


class PasswordResetChallengeRepository:
    """Repository for password reset challenge CRUD and state operations."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def create_challenge(self, user_id: str, otp: str) -> PasswordResetChallenge:
        """Create a new password reset challenge for a user.

        Atomically creates a challenge and invalidates any existing
        unconsumed challenges for the same user.

        Args:
            user_id: The user's UUID string.
            otp: The plaintext 6-digit OTP to hash and store.

        Returns:
            The newly created PasswordResetChallenge instance.

        Raises:
            SQLAlchemyError: If database operations fail.
        """
        otp_hash = hash_otp(otp)
        try:
            # Revoke all existing unconsumed challenges for this user
            self._session_factory.execute(
                update(PasswordResetChallenge)
                .where(
                    PasswordResetChallenge.user_id == user_id,
                    PasswordResetChallenge.is_consumed == 0,
                    PasswordResetChallenge.is_revoked == 0,
                )
                .values(is_revoked=1)
            )

            # Because the table has a hard UNIQUE constraint on user_id, we can
            # only ever have one row per user.  We UPDATE-or-INSERT: try an
            # update first (for the existing revoked row), then INSERT if no
            # row exists at all.
            cooldown_until = (
                datetime.now(timezone.utc) + timedelta(seconds=RESEND_COOLDOWN_SECONDS)
            )

            result = self._session_factory.execute(
                update(PasswordResetChallenge)
                .where(PasswordResetChallenge.user_id == user_id)
                .values(
                    otp_hash=otp_hash,
                    is_consumed=0,
                    is_revoked=0,
                    verification_attempts=0,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
                    resend_cooldown_until=cooldown_until,
                )
                .returning(PasswordResetChallenge.id)
            )
            challenge_id = result.scalar_one_or_none()

            if challenge_id is None:
                challenge = PasswordResetChallenge(
                    user_id=user_id,
                    otp_hash=otp_hash,
                    resend_cooldown_until=cooldown_until,
                )
                self._session_factory.add(challenge)
                self._session_factory.flush()
                challenge_id = challenge.id

            self._session_factory.commit()

            # Re-fetch to return a fully-populated instance (with expires_at, etc.)
            challenge = self._session_factory.execute(
                select(PasswordResetChallenge).where(
                    PasswordResetChallenge.id == challenge_id
                )
            ).scalars().first()

            return challenge
        except SQLAlchemyError:
            self._session_factory.rollback()
            raise

    def get_active_challenge(self, user_id: str) -> PasswordResetChallenge | None:
        """Get the active (unconsumed, not revoked, not expired) challenge for a user.

        Args:
            user_id: The user's UUID string.

        Returns:
            The active PasswordResetChallenge instance, or None if no active
            challenge exists.
        """
        result = self._session_factory.execute(
            select(PasswordResetChallenge).where(
                PasswordResetChallenge.user_id == user_id,
                PasswordResetChallenge.is_consumed == 0,
                PasswordResetChallenge.is_revoked == 0,
            )
        )
        return result.scalars().first()

    def consume_challenge(self, challenge_id: str) -> bool:
        """Atomically mark a challenge as consumed.

        Uses a single UPDATE statement with a WHERE clause that checks
        the challenge is not already consumed/revoked. Returns True if
        the update succeeded (challenge was active and is now consumed).

        Args:
            challenge_id: The UUID string of the challenge to consume.

        Returns:
            True if the challenge was successfully consumed, False if it
            was already consumed or revoked.
        """
        try:
            result = self._session_factory.execute(
                update(PasswordResetChallenge)
                .where(
                    PasswordResetChallenge.id == challenge_id,
                    PasswordResetChallenge.is_consumed == 0,
                    PasswordResetChallenge.is_revoked == 0,
                )
                .values(is_consumed=1)
                .returning(PasswordResetChallenge.id)
            )
            consumed_id = result.scalar_one_or_none()
            self._session_factory.commit()
            return consumed_id is not None
        except SQLAlchemyError:
            self._session_factory.rollback()
            raise

    def revoke_challenge(self, challenge_id: str) -> None:
        """Atomically revoke a challenge.

        Marks a challenge as revoked without consuming it. Use this
        when resetting or invalidating a challenge.

        Args:
            challenge_id: The UUID string of the challenge to revoke.
        """
        try:
            self._session_factory.execute(
                update(PasswordResetChallenge)
                .where(PasswordResetChallenge.id == challenge_id)
                .values(is_revoked=1)
            )
            self._session_factory.commit()
        except SQLAlchemyError:
            self._session_factory.rollback()
            raise

    def revoke_challenges_for_user(self, user_id: str) -> None:
        """Atomically revoke all outstanding challenges for a user.

        Used when a password is successfully reset to invalidate
        all active reset challenges.

        Args:
            user_id: The user's UUID string.
        """
        try:
            self._session_factory.execute(
                update(PasswordResetChallenge)
                .where(
                    PasswordResetChallenge.user_id == user_id,
                    PasswordResetChallenge.is_consumed == 0,
                    PasswordResetChallenge.is_revoked == 0,
                )
                .values(is_revoked=1)
            )
            self._session_factory.commit()
        except SQLAlchemyError:
            self._session_factory.rollback()
            raise

    def increment_attempts(self, challenge_id: str) -> int:
        """Atomically increment the verification attempt count.

        Args:
            challenge_id: The UUID string of the challenge.

        Returns:
            The new verification attempt count after incrementing.
        """
        try:
            result = self._session_factory.execute(
                update(PasswordResetChallenge)
                .where(PasswordResetChallenge.id == challenge_id)
                .values(verification_attempts=PasswordResetChallenge.verification_attempts + 1)
                .returning(PasswordResetChallenge.verification_attempts)
            )
            new_count = result.scalar_one()
            self._session_factory.commit()
            return new_count
        except SQLAlchemyError:
            self._session_factory.rollback()
            raise

    def get_challenge(self, challenge_id: str) -> PasswordResetChallenge | None:
        """Get a challenge by its ID.

        Args:
            challenge_id: The UUID string of the challenge.

        Returns:
            The PasswordResetChallenge instance, or None if not found.
        """
        result = self._session_factory.execute(
            select(PasswordResetChallenge).where(PasswordResetChallenge.id == challenge_id)
        )
        return result.scalars().first()