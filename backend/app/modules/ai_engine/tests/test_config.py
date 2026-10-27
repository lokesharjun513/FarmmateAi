import pytest
from pydantic import ValidationError

from app.core.config import Settings

BASE_SETTINGS = {
    "DATABASE_URL": "sqlite://",
    "JWT_SECRET_KEY": "test-jwt-secret",
}


@pytest.mark.parametrize(
    "missing",
    [
        "AI_API_URL",
        "AI_API_KEY",
        "AI_MODEL",
    ],
)
def test_missing_ai_setting_fails(
    monkeypatch,
    missing,
):

    monkeypatch.delenv(
        missing,
        raising=False,
    )

    with pytest.raises(
        ValidationError,
    ) as exc_info:

        Settings(
            _env_file=None,
            **BASE_SETTINGS,
        )

    assert missing in str(exc_info.value)


def test_blank_ai_setting_fails():

    with pytest.raises(
        ValidationError,
    ):

        Settings(
            _env_file=None,
            DATABASE_URL="sqlite://",
            JWT_SECRET_KEY="test-jwt-secret",
            AI_API_URL="",
            AI_API_KEY="",
            AI_MODEL="",
        )


def test_api_key_is_not_exposed():

    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite://",
        JWT_SECRET_KEY="test-jwt-secret",
        AI_API_URL="https://ai.example.test/v1",
        AI_API_KEY="super-secret-key",
        AI_MODEL="test-model",
    )

    assert "super-secret-key" not in repr(settings)
    assert "super-secret-key" not in str(settings.AI_API_KEY)
