from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==========================
    # Application
    # ==========================

    APP_NAME: str = "FarmMate AI"
    APP_VERSION: str = "1.0.0"

    APP_ENV: Literal[
        "development",
        "testing",
        "staging",
        "production",
    ] = "development"

    # ==========================
    # Database
    # ==========================

    DATABASE_URL: str

    # ==========================
    # JWT
    # ==========================

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ==========================
    # AI
    # ==========================

    AI_API_URL: str = Field(min_length=1)
    AI_API_KEY: SecretStr = Field(min_length=1)
    AI_MODEL: str = Field(min_length=1)

    AI_TEMPERATURE: float = 0.2
    AI_MAX_TOKENS: int = 4096
    AI_REQUEST_TIMEOUT: float = 60.0

    CROP_PLAN_MAX_TOKENS: int = 6000

    # ==========================
    # Firebase Admin
    # ==========================

    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: str | None = None

    # ==========================
    # Storage
    # ==========================

    UPLOAD_DIR: str = "uploads"

    # ==========================
    # Logging
    # ==========================

    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"

    # ==========================
    # Environment configuration
    # ==========================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()