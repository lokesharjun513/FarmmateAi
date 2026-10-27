from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.modules.identity.jwt import decode_access_token
from app.modules.identity.models import User
from app.modules.identity.repository import UserRepository


# ============================================================
# HTTP BEARER SECURITY
# ============================================================

security = HTTPBearer(
    auto_error=False,
)


# ============================================================
# AUTHENTICATION ERROR
# ============================================================


def _credentials_exception() -> HTTPException:
    """
    Standard authentication error used when the access token
    is missing, invalid, expired, malformed, or belongs to
    an unavailable user.
    """

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


# ============================================================
# GET CURRENT USER
# ============================================================


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security,
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the authenticated user from the Bearer token.

    Authentication flow:

        Authorization header
                ↓
        Extract Bearer token
                ↓
        Decode JWT
                ↓
        Validate token type
                ↓
        Validate subject
                ↓
        Convert subject to UUID
                ↓
        Load user from database
                ↓
        Check account status
                ↓
        Return User
    """

    credentials_exception = _credentials_exception()

    # --------------------------------------------------------
    # Authorization header must exist.
    # --------------------------------------------------------

    if credentials is None:
        raise credentials_exception

    # --------------------------------------------------------
    # HTTPBearer already validates the scheme.
    #
    # We explicitly verify it here for clarity.
    # --------------------------------------------------------

    if credentials.scheme.lower() != "bearer":
        raise credentials_exception

    token = credentials.credentials

    if not token:
        raise credentials_exception

    # --------------------------------------------------------
    # Decode and validate JWT.
    #
    # decode_access_token() is the single source of truth
    # for JWT validation.
    # --------------------------------------------------------

    try:

        payload = decode_access_token(
            token,
        )

    except (JWTError, ValueError):

        raise credentials_exception

    # --------------------------------------------------------
    # Validate token type.
    #
    # Access tokens must contain:
    #
    #     type = "access"
    #
    # This prevents other future token types from being
    # accepted as authentication tokens.
    # --------------------------------------------------------

    token_type = payload.get("type")

    if token_type != "access":
        raise credentials_exception

    # --------------------------------------------------------
    # Get subject.
    #
    # `sub` contains the user's UUID as a string.
    # --------------------------------------------------------

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    # --------------------------------------------------------
    # Validate UUID.
    # --------------------------------------------------------

    try:

        user_uuid = UUID(
            str(user_id),
        )

    except (ValueError, TypeError):

        raise credentials_exception

    # --------------------------------------------------------
    # Load user from database.
    # --------------------------------------------------------

    repository = UserRepository(
        db,
    )

    user = repository.get_by_id(
        user_uuid,
    )

    # --------------------------------------------------------
    # User must still exist.
    # --------------------------------------------------------

    if user is None:
        raise credentials_exception

    # --------------------------------------------------------
    # Disabled users cannot use previously issued tokens.
    # --------------------------------------------------------

    if not user.is_active:
        raise credentials_exception

    return user