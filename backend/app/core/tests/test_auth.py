from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import get_current_user
from app.modules.identity.jwt import (
    create_access_token,
)
from app.modules.identity.models import User
from app.modules.identity.security import hash_password


# ============================================================
# HELPERS
# ============================================================


def create_test_user(
    db,
    *,
    is_active=True,
):
    user = User(
        id=uuid4(),
        full_name="Auth Test User",
        mobile=f"{uuid4().hex[:10]}",
        email=f"{uuid4().hex[:10]}@test.com",
        password_hash=hash_password(
            "SecurePassword123!",
        ),
        is_active=is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def credentials_for_token(token: str):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


# ============================================================
# AUTHENTICATION ERROR
# ============================================================


def test_missing_credentials_fails(db):
    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=None,
            db=db,
        )

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == (
        "Invalid or expired access token."
    )

    assert (
        exc_info.value.headers["WWW-Authenticate"]
        == "Bearer"
    )


# ============================================================
# INVALID TOKEN
# ============================================================


def test_invalid_token_fails(db):
    credentials = credentials_for_token(
        "this-is-not-a-valid-jwt",
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == (
        "Invalid or expired access token."
    )


def test_empty_token_fails(db):
    credentials = credentials_for_token("")

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


# ============================================================
# VALID TOKEN
# ============================================================


def test_valid_access_token_returns_user(db):
    user = create_test_user(db)

    token = create_access_token(
        str(user.id),
    )

    credentials = credentials_for_token(token)

    current_user = get_current_user(
        credentials=credentials,
        db=db,
    )

    assert current_user.id == user.id

    assert current_user.email == user.email

    assert current_user.mobile == user.mobile


# ============================================================
# USER NOT FOUND
# ============================================================


def test_token_for_nonexistent_user_fails(db):
    fake_user_id = uuid4()

    token = create_access_token(
        str(fake_user_id),
    )

    credentials = credentials_for_token(token)

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == (
        "Invalid or expired access token."
    )


# ============================================================
# INACTIVE USER
# ============================================================


def test_inactive_user_cannot_authenticate(db):
    user = create_test_user(
        db,
        is_active=False,
    )

    token = create_access_token(
        str(user.id),
    )

    credentials = credentials_for_token(token)

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == (
        "Invalid or expired access token."
    )


# ============================================================
# TOKEN TYPE
# ============================================================


def test_non_access_token_is_rejected(
    db,
    monkeypatch,
):
    user = create_test_user(db)

    def fake_decode_access_token(token):
        return {
            "sub": str(user.id),
            "type": "refresh",
        }

    monkeypatch.setattr(
        "app.core.auth.decode_access_token",
        fake_decode_access_token,
    )

    credentials = credentials_for_token(
        "fake-refresh-token",
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_missing_token_type_is_rejected(
    db,
    monkeypatch,
):
    user = create_test_user(db)

    def fake_decode_access_token(token):
        return {
            "sub": str(user.id),
        }

    monkeypatch.setattr(
        "app.core.auth.decode_access_token",
        fake_decode_access_token,
    )

    credentials = credentials_for_token(
        "fake-token",
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


# ============================================================
# SUBJECT
# ============================================================


def test_missing_subject_is_rejected(
    db,
    monkeypatch,
):
    def fake_decode_access_token(token):
        return {
            "type": "access",
        }

    monkeypatch.setattr(
        "app.core.auth.decode_access_token",
        fake_decode_access_token,
    )

    credentials = credentials_for_token(
        "fake-token",
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_invalid_uuid_subject_is_rejected(
    db,
    monkeypatch,
):
    def fake_decode_access_token(token):
        return {
            "sub": "not-a-valid-uuid",
            "type": "access",
        }

    monkeypatch.setattr(
        "app.core.auth.decode_access_token",
        fake_decode_access_token,
    )

    credentials = credentials_for_token(
        "fake-token",
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_empty_subject_is_rejected(
    db,
    monkeypatch,
):
    def fake_decode_access_token(token):
        return {
            "sub": "",
            "type": "access",
        }

    monkeypatch.setattr(
        "app.core.auth.decode_access_token",
        fake_decode_access_token,
    )

    credentials = credentials_for_token(
        "fake-token",
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


# ============================================================
# TOKEN DECODING FAILURE
# ============================================================


def test_decode_value_error_becomes_401(
    db,
    monkeypatch,
):
    def fake_decode_access_token(token):
        raise ValueError(
            "Invalid or expired token.",
        )

    monkeypatch.setattr(
        "app.core.auth.decode_access_token",
        fake_decode_access_token,
    )

    credentials = credentials_for_token(
        "fake-token",
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


# ============================================================
# BEARER SCHEME
# ============================================================


def test_non_bearer_scheme_is_rejected(db):
    user = create_test_user(db)

    token = create_access_token(
        str(user.id),
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Basic",
        credentials=token,
    )

    with pytest.raises(HTTPException) as exc_info:

        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_bearer_scheme_is_case_insensitive(db):
    user = create_test_user(db)

    token = create_access_token(
        str(user.id),
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="BEARER",
        credentials=token,
    )

    current_user = get_current_user(
        credentials=credentials,
        db=db,
    )

    assert current_user.id == user.id