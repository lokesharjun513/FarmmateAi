from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.ai_engine.providers.ai_provider import AIProviderError
from app.shared.exceptions import (
    ActivityNotFoundError,
    CropSeasonNotFoundError,
    EmailAlreadyExistsError,
    FarmAccessDeniedError,
    FarmerProfileAlreadyExistsError,
    FarmerProfileNotFoundError,
    FarmNotFoundError,
    InvalidCredentialsError,
    MobileAlreadyExistsError,
    UnauthorizedError,
    ValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(EmailAlreadyExistsError)
    async def email_exists_exception_handler(
        request: Request,
        exc: EmailAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "message": "Email already exists.",
                "errors": [],
            },
        )

    @app.exception_handler(MobileAlreadyExistsError)
    async def mobile_exists_exception_handler(
        request: Request,
        exc: MobileAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "message": "Mobile number already exists.",
                "errors": [],
            },
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_exception_handler(
        request: Request,
        exc: InvalidCredentialsError,
    ):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid email/mobile or password.",
                "errors": [],
            },
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_exception_handler(
        request: Request,
        exc: UnauthorizedError,
    ):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Authentication required.",
                "errors": [],
            },
        )

    @app.exception_handler(FarmerProfileAlreadyExistsError)
    async def farmer_profile_exists_exception_handler(
        request: Request,
        exc: FarmerProfileAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "message": "Farmer profile already exists.",
                "errors": [],
            },
        )

    @app.exception_handler(FarmerProfileNotFoundError)
    async def farmer_profile_not_found_exception_handler(
        request: Request,
        exc: FarmerProfileNotFoundError,
    ):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "Farmer profile not found.",
                "errors": [],
            },
        )

    @app.exception_handler(FarmNotFoundError)
    async def farm_not_found_exception_handler(
        request: Request,
        exc: FarmNotFoundError,
    ):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "Farm not found.",
                "errors": [],
            },
        )

    @app.exception_handler(FarmAccessDeniedError)
    async def farm_access_denied_exception_handler(
        request: Request,
        exc: FarmAccessDeniedError,
    ):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "Access denied.",
                "errors": [],
            },
        )

    @app.exception_handler(CropSeasonNotFoundError)
    async def crop_season_not_found_exception_handler(
        request: Request,
        exc: CropSeasonNotFoundError,
    ):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "Crop season not found.",
                "errors": [],
            },
        )

    @app.exception_handler(ActivityNotFoundError)
    async def activity_not_found_exception_handler(
        request: Request,
        exc: ActivityNotFoundError,
    ):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "Activity not found.",
                "errors": [],
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: ValidationError,
    ):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(exc),
                "errors": [],
            },
        )

    @app.exception_handler(AIProviderError)
    async def ai_provider_exception_handler(
        request: Request,
        exc: AIProviderError,
    ):
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "message": (
                    "AI service is temporarily unavailable. "
                    "Please try again."
                ),
                "errors": [],
            },
        )