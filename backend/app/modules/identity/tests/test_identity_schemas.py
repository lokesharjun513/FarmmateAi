import pytest
from pydantic import ValidationError

from app.modules.identity.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenData,
    UserResponse,
)


# ============================================================
# REGISTER
# ============================================================


def test_register_request_valid():

    request = RegisterRequest(
        full_name="Test Farmer",
        mobile="9876543210",
        email="TEST@Example.COM",
        password="password123",
    )

    assert request.full_name == "Test Farmer"
    assert request.mobile == "9876543210"
    assert str(request.email) == "test@example.com"
    assert request.password == "password123"


def test_register_request_trims_full_name():

    request = RegisterRequest(
        full_name="  Test Farmer  ",
        mobile="9876543210",
        email="test@example.com",
        password="password123",
    )

    assert request.full_name == "Test Farmer"


def test_register_request_rejects_empty_name():

    with pytest.raises(ValidationError):

        RegisterRequest(
            full_name="   ",
            mobile="9876543210",
            email="test@example.com",
            password="password123",
        )


def test_register_request_rejects_short_name():

    with pytest.raises(ValidationError):

        RegisterRequest(
            full_name="Ab",
            mobile="9876543210",
            email="test@example.com",
            password="password123",
        )


def test_register_request_rejects_invalid_mobile():

    with pytest.raises(ValidationError):

        RegisterRequest(
            full_name="Test Farmer",
            mobile="12345",
            email="test@example.com",
            password="password123",
        )


def test_register_request_rejects_non_numeric_mobile():

    with pytest.raises(ValidationError):

        RegisterRequest(
            full_name="Test Farmer",
            mobile="abcdefghij",
            email="test@example.com",
            password="password123",
        )


def test_register_request_rejects_invalid_email():

    with pytest.raises(ValidationError):

        RegisterRequest(
            full_name="Test Farmer",
            mobile="9876543210",
            email="invalid-email",
            password="password123",
        )


def test_register_request_rejects_short_password():

    with pytest.raises(ValidationError):

        RegisterRequest(
            full_name="Test Farmer",
            mobile="9876543210",
            email="test@example.com",
            password="1234567",
        )


def test_register_request_rejects_long_password():

    with pytest.raises(ValidationError):

        RegisterRequest(
            full_name="Test Farmer",
            mobile="9876543210",
            email="test@example.com",
            password="a" * 129,
        )


# ============================================================
# LOGIN
# ============================================================


def test_login_request_valid():

    request = LoginRequest(
        identifier=" TEST@Example.COM ",
        password="password123",
    )

    assert request.identifier == "test@example.com"
    assert request.password == "password123"


def test_login_request_normalizes_identifier():

    request = LoginRequest(
        identifier=" 9876543210 ",
        password="password123",
    )

    assert request.identifier == "9876543210"


def test_login_request_requires_identifier():

    with pytest.raises(ValidationError):

        LoginRequest(
            identifier="",
            password="password123",
        )


def test_login_request_requires_password():

    with pytest.raises(ValidationError):

        LoginRequest(
            identifier="test@example.com",
            password="",
        )


# ============================================================
# TOKEN DATA
# ============================================================


def test_token_data_default_token_type():

    token = TokenData(
        access_token="test-token",
    )

    assert token.access_token == "test-token"
    assert token.token_type == "bearer"


# ============================================================
# USER RESPONSE
# ============================================================


def test_user_response_from_attributes():

    class FakeUser:

        id = "00000000-0000-0000-0000-000000000001"
        full_name = "Test Farmer"
        mobile = "9876543210"
        email = "test@example.com"
        is_active = True

    response = UserResponse.model_validate(
        FakeUser(),
    )

    assert response.full_name == "Test Farmer"
    assert response.mobile == "9876543210"
    assert str(response.email) == "test@example.com"
    assert response.is_active is True