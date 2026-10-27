from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings


# ============================================================
# TOKEN PAYLOAD
# ============================================================


def create_token_payload(user_id: str) -> dict:
    """
    Create the payload used for an access token.
    """

    now = datetime.now(UTC)

    expire = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return {
        # ----------------------------------------------------
        # User identifier
        # ----------------------------------------------------

        "sub": user_id,

        # ----------------------------------------------------
        # Token issued-at time
        # ----------------------------------------------------

        "iat": now,

        # ----------------------------------------------------
        # Token expiration time
        # ----------------------------------------------------

        "exp": expire,

        # ----------------------------------------------------
        # Unique token identifier
        # ----------------------------------------------------

        "jti": str(uuid4()),

        # ----------------------------------------------------
        # Token type
        #
        # Used by core.auth to ensure that only access tokens
        # can authenticate API requests.
        # ----------------------------------------------------

        "type": "access",
    }


# ============================================================
# CREATE ACCESS TOKEN
# ============================================================


def create_access_token(user_id: str) -> str:
    """
    Create a signed JWT access token for a user.
    """

    payload = create_token_payload(user_id)

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ============================================================
# DECODE ACCESS TOKEN
# ============================================================


def decode_access_token(token: str) -> dict:
    """
    Decode and cryptographically verify an access token.

    Raises:
        ValueError:
            If the token is invalid, expired, or does not
            contain a valid subject.
    """

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM,
            ],
        )

        # ----------------------------------------------------
        # A valid access token must contain a subject.
        # ----------------------------------------------------

        subject = payload.get("sub")

        if not subject:
            raise ValueError(
                "Token subject is missing.",
            )

        return payload

    except JWTError as exc:

        raise ValueError(
            "Invalid or expired token.",
        ) from exc