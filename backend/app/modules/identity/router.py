from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.modules.identity.models import User

from app.database.session import get_db
from app.modules.identity.repository import UserRepository


from app.modules.identity.service import register_user

from app.modules.identity.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenData,
    UserResponse,
)

from app.modules.identity.service import login_user


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

@router.get("/me", response_model=RegisterResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return RegisterResponse(
        success=True,
        message="User retrieved successfully.",
        data=UserResponse.model_validate(current_user),
    )