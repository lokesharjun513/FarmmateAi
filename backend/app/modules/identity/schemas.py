from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.shared.responses import ApiResponse


# ============================================================
# REGISTER
# ============================================================


class RegisterRequest(BaseModel):

    full_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    mobile: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Full name cannot be empty."
            )

        return value

    @field_validator("mobile")
    @classmethod
    def normalize_mobile(
        cls,
        value: str,
    ) -> str:

        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr,
    ) -> EmailStr:

        return value.lower()


# ============================================================
# LOGIN
# ============================================================


class LoginRequest(BaseModel):

    identifier: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(
        cls,
        value: str,
    ) -> str:

        return value.strip().lower()


# ============================================================
# USER RESPONSE
# ============================================================


class UserResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    full_name: str

    mobile: str

    email: EmailStr

    is_active: bool


# ============================================================
# TOKEN DATA
# ============================================================


class TokenData(BaseModel):

    access_token: str

    token_type: str = "bearer"


# ============================================================
# FORGOT PASSWORD
# ============================================================


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] # Changed from dict[str, str] to dict[str, Any] to accommodate optional keys


# ============================================================
# VERIFY RESET OTP
# ============================================================


class VerifyResetOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


class VerifyResetOtpResponse(BaseModel):
    success: bool
    data: dict[str, str]


# ============================================================
# RESEND RESET OTP
# ============================================================


class ResendResetOtpRequest(BaseModel):
    email: EmailStr


class ResendResetOtpResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, str]


# ============================================================
# RESET PASSWORD
# ============================================================


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str


# ============================================================
# API RESPONSES
# ============================================================


RegisterResponse = ApiResponse[UserResponse]

LoginResponse = ApiResponse[TokenData]