from app.modules.identity.jwt import create_access_token
from app.modules.identity.models import User
from app.modules.identity.repository import UserRepository
from app.modules.identity.schemas import RegisterRequest
from app.modules.identity.security import (
    hash_password,
    verify_password,
)

from app.shared.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    MobileAlreadyExistsError,
)


# ============================================================
# REGISTER USER
# ============================================================


def register_user(
    repository: UserRepository,
    request: RegisterRequest,
) -> User:
    """
    Register a new user account.

    Registration is responsible only for creating the
    authentication identity.

    Farmer profile creation is handled separately by the
    farmer/onboarding workflow.
    """

    # --------------------------------------------------------
    # Check whether email is already registered.
    # --------------------------------------------------------

    if repository.get_by_email(request.email):
        raise EmailAlreadyExistsError()

    # --------------------------------------------------------
    # Check whether mobile is already registered.
    # --------------------------------------------------------

    if repository.get_by_mobile(request.mobile):
        raise MobileAlreadyExistsError()

    # --------------------------------------------------------
    # Create user.
    #
    # Never store the plain-text password.
    # --------------------------------------------------------

    user = User(
        full_name=request.full_name,
        mobile=request.mobile,
        email=str(request.email).lower(),
        password_hash=hash_password(request.password),
    )

    return repository.create(user)


# ============================================================
# LOGIN USER
# ============================================================


def login_user(
    repository: UserRepository,
    identifier: str,
    password: str,
) -> str:
    """
    Authenticate a user using email or mobile.

    Returns:
        JWT access token.

    Raises:
        InvalidCredentialsError:
            When the credentials are invalid or the account
            is inactive.
    """

    # --------------------------------------------------------
    # Normalize identifier.
    #
    # Email is case-insensitive.
    # Mobile is stored in normalized form.
    # --------------------------------------------------------

    identifier = identifier.strip().lower()

    # --------------------------------------------------------
    # Find user by email or mobile.
    # --------------------------------------------------------

    user = repository.get_by_identifier(identifier)

    # --------------------------------------------------------
    # Do not reveal whether the identifier exists.
    #
    # Both invalid identifier and invalid password return
    # the same authentication error.
    # --------------------------------------------------------

    if not user:
        raise InvalidCredentialsError()

    # --------------------------------------------------------
    # Reject disabled accounts.
    # --------------------------------------------------------

    if not user.is_active:
        raise InvalidCredentialsError()

    # --------------------------------------------------------
    # Verify password against stored password hash.
    # --------------------------------------------------------

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise InvalidCredentialsError()

    # --------------------------------------------------------
    # Generate access token.
    # --------------------------------------------------------

    return create_access_token(
        str(user.id),
    )