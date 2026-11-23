from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings


# ============================================================
# TOKEN PAYLOAD
# ============================================================


def create_token_payload(user_id: str, *, type: str = "access", minutes: int | None = None) -> dict:
    """Create the payload used for a JWT token.

    Args:
        user_id: The user's UUID string.
        type: Token type ("access" or "password_reset").
        minutes: Expiry in minutes. If None, uses ACCESS_TOKEN_EXPIRE_MINUTES.
    """

    now = datetime.now(UTC)

    expire_minutes = minutes if minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES

    expire = now + timedelta(minutes=expire_minutes)

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

        "type": type,
    }


# ============================================================
# CREATE ACCESS TOKEN
# ============================================================


def create_access_token(user_id: str, *, payload: dict | None = None) -> str:
    """Create a signed JWT access token for a user.

    Args:
        user_id: The user's UUID string.
        payload: Optional custom payload. If None, a default payload
            is created with access token expiry.
    """

    if payload is not None:
        encoded_payload = payload
    else:
        encoded_payload = create_token_payload(user_id)

    return jwt.encode(
        encoded_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ============================================================
# DECODE ACCESS TOKEN
# ============================================================


def decode_access_token(token: str) -> dict:
    """Decode and cryptographically verify an access token.

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