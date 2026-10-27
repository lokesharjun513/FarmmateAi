from uuid import uuid4

import pytest

from app.modules.identity.models import User
from app.modules.identity.repository import UserRepository
from app.modules.identity.schemas import RegisterRequest
from app.modules.identity.service import (
    register_user,
    login_user,
)

from app.shared.exceptions import (
    EmailAlreadyExistsError,
    MobileAlreadyExistsError,
    InvalidCredentialsError,
)


# ============================================================
# HELPERS
# ============================================================


def register_request(
    *,
    full_name="Test Farmer",
    mobile="9876543210",
    email="test@example.com",
    password="password123",
):

    return RegisterRequest(
        full_name=full_name,
        mobile=mobile,
        email=email,
        password=password,
    )


# ============================================================
# REGISTER
# ============================================================


def test_register_user(db):

    repository = UserRepository(db)

    request = register_request()

    user = register_user(
        repository,
        request,
    )

    assert user.id is not None
    assert user.full_name == "Test Farmer"
    assert user.mobile == "9876543210"
    assert user.email == "test@example.com"
    assert user.password_hash != "password123"
    assert user.is_active is True


def test_register_user_hashes_password(db):

    repository = UserRepository(db)

    request = register_request(
        password="my-secret-password",
    )

    user = register_user(
        repository,
        request,
    )

    assert user.password_hash != "my-secret-password"


def test_register_duplicate_email(db):

    repository = UserRepository(db)

    register_user(
        repository,
        register_request(),
    )

    with pytest.raises(
        EmailAlreadyExistsError,
    ):

        register_user(
            repository,
            register_request(
                mobile="9999999999",
                email="TEST@EXAMPLE.COM",
            ),
        )


def test_register_duplicate_mobile(db):

    repository = UserRepository(db)

    register_user(
        repository,
        register_request(),
    )

    with pytest.raises(
        MobileAlreadyExistsError,
    ):

        register_user(
            repository,
            register_request(
                mobile="9876543210",
                email="other@example.com",
            ),
        )


# ============================================================
# LOGIN
# ============================================================


def test_login_with_email(db):

    repository = UserRepository(db)

    register_user(
        repository,
        register_request(),
    )

    token = login_user(
        repository,
        "test@example.com",
        "password123",
    )

    assert isinstance(token, str)
    assert token


def test_login_with_mobile(db):

    repository = UserRepository(db)

    register_user(
        repository,
        register_request(),
    )

    token = login_user(
        repository,
        "9876543210",
        "password123",
    )

    assert isinstance(token, str)
    assert token


def test_login_normalizes_identifier(db):

    repository = UserRepository(db)

    register_user(
        repository,
        register_request(),
    )

    token = login_user(
        repository,
        "  TEST@EXAMPLE.COM ",
        "password123",
    )

    assert token


def test_login_invalid_identifier(db):

    repository = UserRepository(db)

    with pytest.raises(
        InvalidCredentialsError,
    ):

        login_user(
            repository,
            "missing@example.com",
            "password123",
        )


def test_login_invalid_password(db):

    repository = UserRepository(db)

    register_user(
        repository,
        register_request(),
    )

    with pytest.raises(
        InvalidCredentialsError,
    ):

        login_user(
            repository,
            "test@example.com",
            "wrong-password",
        )


def test_login_inactive_user(db):

    repository = UserRepository(db)

    user = register_user(
        repository,
        register_request(),
    )

    user.is_active = False

    db.commit()

    with pytest.raises(
        InvalidCredentialsError,
    ):

        login_user(
            repository,
            "test@example.com",
            "password123",
        )