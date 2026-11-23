"""Tests for OTP hashing (HMAC) and SMTP-failure behaviour.

The OTP is stored as a server-keyed HMAC-SHA256 digest, never plaintext.
These tests pin down the round-trip contract and the generic-enough
response when email delivery fails (no account enumeration, no crash).
"""

import re

from unittest.mock import MagicMock, patch

from app.modules.password_reset.models import (
    generate_otp,
    hash_otp,
    verify_otp,
)
from app.modules.password_reset.service import (
    SmtpEmailError,
    forgot_password,
)


def test_generate_otp_is_six_digits():
    otp = generate_otp()
    assert re.fullmatch(r"\d{6}", otp), otp


def test_otp_round_trip_verify():
    otp = generate_otp()
    digest = hash_otp(otp)
    assert verify_otp(otp, digest) is True
    assert verify_otp("000000", digest) is False


def test_otp_hash_is_not_plaintext():
    otp = "123456"
    digest = hash_otp(otp)
    assert digest != otp
    assert "123456" not in digest


def test_otp_verify_matches_correct_digest_only():
    otp = "987654"
    quiet = hash_otp("987655")
    assert verify_otp(otp, quiet) is False


def test_forgot_password_returns_generic_status_when_smtp_fails():
    """SMTP failure must not 500 or expose state; caller sees 'sent'."""
    fake_user = MagicMock()
    fake_user.id = "00000000-0000-0000-0000-000000000001"
    fake_user.email = "carrier@example.com"
    fake_user.is_active = True

    fake_challenge = MagicMock()
    fake_challenge.can_resend.return_value = True
    fake_challenge.resend_cooldown_until = None

    with (
        patch(
            "app.modules.identity.repository.UserRepository",
        ) as mock_user_repo_cls,
        patch(
            "app.modules.password_reset.repository.PasswordResetChallengeRepository",
        ) as mock_repo_cls,
        patch(
            "app.modules.password_reset.service.send_password_reset_otp",
            side_effect=SmtpEmailError("boom"),
        ),
    ):
        mock_user_repo_cls.return_value.get_by_email.return_value = fake_user
        mock_repo_cls.return_value.get_active_challenge.return_value = fake_challenge
        mock_repo_cls.return_value.create_challenge.return_value = fake_challenge

        result = forgot_password(fake_user.email, db=MagicMock())

    assert result["status"] == "sent"
    assert "reset code has been sent" in result["detail"]
