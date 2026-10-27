from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from app.core.config import settings
from app.modules.identity.jwt import (
    create_token_payload,
    create_access_token,
    decode_access_token,
)


# ============================================================
# PAYLOAD
# ============================================================


def test_create_token_payload():

    user_id = str(uuid4())

    payload = create_token_payload(
        user_id,
    )

    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload
    assert "jti" in payload


def test_token_has_expiration():

    user_id = str(uuid4())

    payload = create_token_payload(
        user_id,
    )

    assert payload["exp"] > payload["iat"]


# ============================================================
# CREATE TOKEN
# ============================================================


def test_create_access_token():

    user_id = str(uuid4())

    token = create_access_token(
        user_id,
    )

    assert isinstance(token, str)
    assert token.count(".") == 2


# ============================================================
# DECODE TOKEN
# ============================================================


def test_decode_access_token():

    user_id = str(uuid4())

    token = create_access_token(
        user_id,
    )

    payload = decode_access_token(
        token,
    )

    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_decode_invalid_token():

    with pytest.raises(ValueError):

        decode_access_token(
            "invalid.token.value",
        )


def test_decode_expired_token():

    now = datetime.now(UTC)

    payload = {
        "sub": str(uuid4()),
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=5),
        "jti": str(uuid4()),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(ValueError):

        decode_access_token(
            token,
        )


def test_decode_token_without_subject():

    now = datetime.now(UTC)

    payload = {
        "iat": now,
        "exp": now + timedelta(minutes=10),
        "jti": str(uuid4()),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(ValueError):

        decode_access_token(
            token,
        )