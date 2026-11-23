from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.modules.identity.models import User

from app.database.session import get_db
from app.modules.identity.repository import UserRepository

from app.modules.password_reset.service import (
    forgot_password,
    verify_reset_otp,
    resend_reset_otp,
    reset_password,
)
from app.modules.identity.service import register_user, login_user

from app.modules.identity.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenData,
    UserResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetOtpRequest,
    VerifyResetOtpResponse,
    ResendResetOtpRequest,
    ResendResetOtpResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", response_model=RegisterResponse)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)

    user = register_user(repository, request)

    return RegisterResponse(
        success=True,
        message="User registered successfully.",
        data=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)

    token = login_user(
        repository,
        request.identifier,
        request.password,
    )

    return LoginResponse(
        success=True,
        message="Login successful.",
        data=TokenData(
            access_token=token,
        ),
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password_endpoint(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    result = forgot_password(request.email, db)

    # Construct response data dict preserving any optional keys like resend_cooldown_until
    response_data = {'status': result['status']}
    if 'resend_cooldown_until' in result:
        response_data['resend_cooldown_until'] = result['resend_cooldown_until']

    return ForgotPasswordResponse(
        success=True,
        message=result['detail'],
        data=response_data,
    )


@router.post("/verify-reset-otp", response_model=VerifyResetOtpResponse)
def verify_reset_otp_endpoint(
    request: VerifyResetOtpRequest,
    db: Session = Depends(get_db),
):
    result = verify_reset_otp(email=request.email, otp=request.otp, db=db)
    if result is None:
        # Generic message: never reveal whether the account exists,
        # whether the challenge expired, or how many attempts remain.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )
    return VerifyResetOtpResponse(
        success=True,
        data={'reset_authorization': result['reset_authorization'], 'expires_at': result['expires_at']},
    )


@router.post("/resend-reset-otp", response_model=ResendResetOtpResponse)
def resend_reset_otp_endpoint(
    request: ResendResetOtpRequest,
    db: Session = Depends(get_db),
):
    result = resend_reset_otp(email=request.email, db=db)

    response_data = {'status': result['status']}
    if 'resend_cooldown_until' in result:
        response_data['resend_cooldown_until'] = result['resend_cooldown_until']

    return ResendResetOtpResponse(
        success=True,
        message=result['detail'],
        data=response_data,
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password_endpoint(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    try:
        result = reset_password(reset_token=request.reset_token, new_password=request.new_password, db=db)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset authorization.",
        )
    return ResetPasswordResponse(
        success=True,
        message=result['detail'],
    )


@router.get("/me", response_model=RegisterResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return RegisterResponse(
        success=True,
        message="User retrieved successfully.",
        data=UserResponse.model_validate(current_user),
    )