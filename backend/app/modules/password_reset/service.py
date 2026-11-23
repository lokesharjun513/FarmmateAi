# Password Reset Service

"""Service layer for password reset operations.

Handles the business logic for the password reset flow including:
- OTP generation and validation
- Challenge management
- SMTP email sending (decoupled from HTTP layer)
- Rate limiting and cooldown enforcement
- Reset authorization management
- Password policy validation

The service is designed to be called from API endpoints and does not
directly handle HTTP requests. It raises specific exceptions that the
API layer translates into appropriate HTTP responses.

Key design principles:
- Never store plaintext OTPs; always hash before persistence
- Use atomic database operations to prevent race conditions
- Rate limit per user account; IP-level rate limiting is handled
  by the API layer/middleware
- Never reveal whether an account exists through error messages
- SMTP failures are caught and reported as generic errors
- Password policy validation uses the existing hashing utility's
  built-in checks where possible
"""

import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

import jwt
from sqlalchemy.exc import SQLAlchemyError

from ...core.config import settings
from ...modules.password_reset.models import (
    PasswordResetChallenge,
    generate_otp,
    hash_otp,
    verify_otp,
)
from ...modules.password_reset.repository import PasswordResetChallengeRepository
from ...modules.identity.models import User
from app.modules.identity.jwt import create_access_token

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SMTP Email Helper
# ---------------------------------------------------------------------------

class SmtpEmailError(Exception):
    """Raised when an email cannot be sent via SMTP."""
    pass


def _get_settings():
    """Retrieve SMTP settings from the application configuration."""
    logger.info(f"Loading SMTP settings: host={settings.SMTP_HOST}, user={settings.SMTP_USER}")
    smtp_settings = {
        "host": settings.SMTP_HOST,
        "port": int(settings.SMTP_PORT),  # Ensure integer
        "username": settings.SMTP_USER,
        "password": settings.SMTP_PASS,
        "from_address": settings.SMTP_FROM,
    }

    missing = [k for k, v in smtp_settings.items() if v is None]
    if missing:
        raise ValueError(f"Missing SMTP settings: {', '.join(missing)}")

    return smtp_settings


def _send_smtp_email(
    smtp_config: dict,
    to_address: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> None:
    """Send an email via SMTP with TLS and proper error handling."""
    host = smtp_config["host"]
    port = smtp_config["port"]
    username = smtp_config["username"]
    password = smtp_config["password"]
    from_address = smtp_config["from_address"]

    msg = EmailMessage()
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    try:
        logger.info("Attempting to connect to SMTP server: %s:%s", host, port)
        server = smtplib.SMTP(host, port, timeout=30)
        server.ehlo()
        logger.info("Starting TLS...")
        server.starttls()
        server.ehlo()
        logger.info("Authenticating...")
        server.login(username, password)
        logger.info("Sending email to %s...", to_address)
        # send_message raises SMTPRecipientsRefused if any recipient is rejected
        server.send_message(msg)
        server.quit()
        logger.info("Email successfully sent to %s", to_address)
    except smtplib.SMTPRecipientsRefused as e:
        logger.error("SMTP recipients refused for %s: %s", to_address, e.recipients)
        raise SmtpEmailError(f"SMTP recipients refused: {e.recipients}") from e
    except Exception as e:
        logger.error("SMTP error sending email to %s: %s", to_address, str(e))
        raise SmtpEmailError(f"Failed to send email: {e}") from e


def send_password_reset_otp(email: str, otp: str) -> None:
    """Send a password reset OTP email to the specified address."""
    smtp_config = _get_settings()

    html_content = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;
                padding: 20px; background-color: #fff7f6; border-radius: 8px;">
      <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #174d3a; font-size: 24px; margin: 10px 0;">
          FarmMate AI
        </h1>
      </div>
      <p style="color: #202720; font-size: 16px; line-height: 1.5;">
        Your password reset code is:
      </p>
      <div style="text-align: center; margin: 25px 0;">
        <span style="font-size: 32px; font-weight: bold; color: #174d3a;">
          {otp}
        </span>
      </div>
      <p style="color: #637064; font-size: 14px; line-height: 1.5;">
        This code will expire in 5 minutes.
      </p>
    </div>
    """

    text_content = f"Your password reset code is: {otp}. This code will expire in 5 minutes."

    _send_smtp_email(
        smtp_config=smtp_config,
        to_address=email,
        subject="FarmMate AI — Your Password Reset Code",
        html_content=html_content,
        text_content=text_content,
    )


def send_password_changed_notification(email: str, changed_at: Optional[datetime] = None) -> None:
    """Send a password change confirmation email."""
    smtp_config = _get_settings()
    if changed_at is None:
        changed_at = datetime.now(timezone.utc)
    formatted_time = changed_at.strftime("%B %d, %Y at %I:%M %p UTC")

    html_content = f"""
    <div style="font-family: system-ui, sans-serif; padding: 20px;">
      <p>Your password has been successfully changed on {formatted_time}.</p>
    </div>
    """
    text_content = f"Your password has been successfully changed on {formatted_time}."

    _send_smtp_email(
        smtp_config=smtp_config,
        to_address=email,
        subject="FarmMate AI — Your Password Has Been Changed",
        html_content=html_content,
        text_content=text_content,
    )


# ---------------------------------------------------------------------------
# OTP and Challenge Management
# ---------------------------------------------------------------------------

def forgot_password(email: str, db) -> dict:
    """Initiate a password reset flow."""
    normalized_email = email.lower().strip()

    from ...modules.identity.repository import UserRepository
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(normalized_email)

    if user is None or not user.is_active:
        return {"status": "sent", "detail": "If an account with that email exists, a reset code has been sent."}

    existing_challenge = PasswordResetChallengeRepository(db).get_active_challenge(str(user.id))

    if existing_challenge and existing_challenge.can_resend() is False:
        return {
            "status": "cooldown",
            "detail": "A reset code has already been sent. Please wait before requesting another.",
            "resend_cooldown_until": existing_challenge.resend_cooldown_until.isoformat()
            if existing_challenge.resend_cooldown_until
            else None,
        }

    otp = generate_otp()
    challenge = PasswordResetChallengeRepository(db).create_challenge(str(user.id), otp)
    try:
        send_password_reset_otp(normalized_email, otp)
    except SmtpEmailError as e:
        # ponytail: generic response preserved to avoid account enumeration;
        # failure is visible in logs only
        logger.error("SMTP submission failed for user lookup %s: %s", user.id, str(e))

    return {
        "status": "sent",
        "detail": "If an account with that email exists, a reset code has been sent.",
        # Server-authoritative retry deadline so the client can start its
        # countdown from the real value instead of a hardcoded 60s.
        "resend_cooldown_until": challenge.resend_cooldown_until.isoformat()
        if challenge.resend_cooldown_until
        else None,
    }


def resend_reset_otp(email: str, db) -> dict:
    """Resend a password reset OTP."""
    return forgot_password(email, db)


def verify_reset_otp(email: str, otp: str, db) -> Optional[dict]:
    """Verify a password reset OTP."""
    normalized_email = email.lower().strip()

    from ...modules.identity.repository import UserRepository
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(normalized_email)

    if user is None:
        return None

    challenge = PasswordResetChallengeRepository(db).get_active_challenge(str(user.id))
    if challenge is None:
        return None

    if challenge.is_expired():
        PasswordResetChallengeRepository(db).consume_challenge(challenge.id)
        return None

    if not challenge.can_verify():
        PasswordResetChallengeRepository(db).consume_challenge(challenge.id)
        return None

    if not verify_otp(otp, challenge.otp_hash):
        PasswordResetChallengeRepository(db).increment_attempts(challenge.id)
        if challenge.verification_attempts + 1 >= challenge.max_attempts:
            PasswordResetChallengeRepository(db).consume_challenge(challenge.id)
        return None

    PasswordResetChallengeRepository(db).consume_challenge(challenge.id)
    reset_token = _issue_reset_authorization(str(user.id))

    return {
        "reset_authorization": reset_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    }


def _issue_reset_authorization(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=10),
        "type": "password_reset",
    }
    return create_access_token(user_id, payload=payload)


def reset_password(reset_token: str, new_password: str, db) -> dict:
    """Reset a user's password."""
    try:
        payload = jwt.decode(
            reset_token,
            key=settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
    except Exception as e:
        raise ValueError("Invalid reset authorization token.") from e

    if payload.get("type") != "password_reset":
        raise ValueError("Invalid reset authorization token.")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid reset authorization token.")

    from ...modules.identity.repository import UserRepository
    from ...modules.identity.security import hash_password

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if user is None:
        raise ValueError("User not found.")

    if not isinstance(new_password, str) or len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    hashed_password = hash_password(new_password)
    user.password_hash = hashed_password
    db.commit()

    PasswordResetChallengeRepository(db).revoke_challenges_for_user(str(user.id))

    import threading
    threading.Thread(target=send_password_changed_notification, args=(user.email,)).start()

    return {"status": "success", "detail": "Password has been changed."}
