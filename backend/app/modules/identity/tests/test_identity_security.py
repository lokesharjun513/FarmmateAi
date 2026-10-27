import bcrypt
import pytest

from app.modules.identity.security import (
    hash_password,
    verify_password,
)


# ============================================================
# HASH PASSWORD
# ============================================================


def test_hash_password_returns_string():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert isinstance(hashed, str)


def test_hash_password_does_not_return_plaintext():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert hashed != password


def test_hash_password_creates_valid_bcrypt_hash():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert hashed.startswith(("$2a$", "$2b$", "$2y$"))

    assert bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8"),
    )


def test_hash_password_generates_different_hash_each_time():
    password = "SecurePassword123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_hash_password_empty_password_fails():
    with pytest.raises(ValueError, match="Password cannot be empty."):
        hash_password("")


def test_hash_password_none_password_fails():
    with pytest.raises(ValueError, match="Password cannot be empty."):
        hash_password(None)


# ============================================================
# VERIFY PASSWORD
# ============================================================


def test_verify_correct_password():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed,
    ) is True


def test_verify_wrong_password():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert verify_password(
        "WrongPassword123!",
        hashed,
    ) is False


def test_verify_empty_password_returns_false():
    hashed = hash_password("SecurePassword123!")

    assert verify_password(
        "",
        hashed,
    ) is False


def test_verify_empty_hash_returns_false():
    assert verify_password(
        "SecurePassword123!",
        "",
    ) is False


def test_verify_both_empty_returns_false():
    assert verify_password(
        "",
        "",
    ) is False


def test_verify_invalid_hash_returns_false():
    assert verify_password(
        "SecurePassword123!",
        "not-a-valid-bcrypt-hash",
    ) is False


def test_verify_corrupted_hash_returns_false():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    corrupted_hash = hashed[:-5] + "xxxxx"

    assert verify_password(
        password,
        corrupted_hash,
    ) is False


def test_verify_does_not_modify_hash():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    original_hash = hashed

    verify_password(
        password,
        hashed,
    )

    assert hashed == original_hash


# ============================================================
# PASSWORD CHARACTER SUPPORT
# ============================================================


def test_password_with_special_characters():
    password = "P@ssw0rd!#$%^&*()"

    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed,
    ) is True


def test_password_with_unicode_characters():
    password = "SecurePassword123!అ"

    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed,
    ) is True