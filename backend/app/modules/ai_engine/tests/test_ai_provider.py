import httpx
import pytest
from pydantic import SecretStr

from app.modules.ai_engine.providers.ai_provider import (
    AIProvider,
    AIProviderError,
)


@pytest.fixture
def provider():
    return AIProvider()


@pytest.fixture
def mock_settings(monkeypatch):

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_API_URL",
        "https://ai.example.test/v1",
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_API_KEY",
        SecretStr("test-api-key"),
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_MODEL",
        "test-model",
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_TEMPERATURE",
        0.2,
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_MAX_TOKENS",
        500,
    )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_REQUEST_TIMEOUT",
        30.0,
    )


@pytest.mark.parametrize(
    ("api_url", "expected_url"),
    [
        (
            "https://ai.example.test/v1",
            "https://ai.example.test/v1/chat/completions",
        ),
        (
            "https://ai.example.test/v1/",
            "https://ai.example.test/v1/chat/completions",
        ),
        (
            "https://ai.example.test/v1/chat/completions",
            "https://ai.example.test/v1/chat/completions",
        ),
        (
            "https://ai.example.test/v1/chat/completions/",
            "https://ai.example.test/v1/chat/completions",
        ),
    ],
)
def test_build_chat_completions_url(
    api_url,
    expected_url,
):

    assert (
        AIProvider._build_chat_completions_url(api_url)
        == expected_url
    )


class MockResponse:

    def __init__(
        self,
        data,
        status_code=200,
    ):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):

        if self.status_code >= 400:

            request = httpx.Request(
                "POST",
                "https://ai.example.test/v1/chat/completions",
            )

            response = httpx.Response(
                self.status_code,
                request=request,
            )

            raise httpx.HTTPStatusError(
                "HTTP error",
                request=request,
                response=response,
            )

    def json(self):

        return self._data


class MockAsyncClient:

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        self.args = args
        self.kwargs = kwargs

        self.post_called = False
        self.post_args = None
        self.post_kwargs = None

    async def __aenter__(self):

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):

        return False

    async def post(
        self,
        *args,
        **kwargs,
    ):

        self.post_called = True
        self.post_args = args
        self.post_kwargs = kwargs

        return MockResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": " AI response "
                        }
                    }
                ]
            }
        )


@pytest.mark.asyncio
async def test_generate_success(
    monkeypatch,
    provider,
    mock_settings,
):

    mock_client = MockAsyncClient()

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: mock_client,
    )

    result = await provider.generate(
        system_prompt="You are FarmMate AI.",
        user_prompt="Give advice for rice.",
    )

    assert result == "AI response"


@pytest.mark.asyncio
async def test_generate_sends_correct_request(
    monkeypatch,
    provider,
    mock_settings,
):

    mock_client = MockAsyncClient()

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: mock_client,
    )

    await provider.generate(
        system_prompt="System prompt",
        user_prompt="User prompt",
    )

    assert mock_client.post_called is True

    assert mock_client.post_args == (
        "https://ai.example.test/v1/chat/completions",
    )

    assert mock_client.post_kwargs["headers"] == {
        "Authorization": "Bearer test-api-key",
        "Content-Type": "application/json",
        "User-Agent": "FarmMateAI/1.0",
    }

    assert mock_client.post_kwargs["json"] == {
        "model": "test-model",
        "messages": [
            {
                "role": "system",
                "content": "System prompt",
            },
            {
                "role": "user",
                "content": "User prompt",
            },
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }


@pytest.mark.asyncio
async def test_generate_uses_custom_temperature_and_max_tokens(
    monkeypatch,
    provider,
    mock_settings,
):

    mock_client = MockAsyncClient()

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: mock_client,
    )

    await provider.generate(
        system_prompt="System",
        user_prompt="User",
        temperature=0.7,
        max_tokens=1000,
    )

    payload = mock_client.post_kwargs["json"]

    assert payload["temperature"] == 0.7
    assert payload["max_tokens"] == 1000


@pytest.mark.asyncio
async def test_generate_uses_settings_when_parameters_are_none(
    monkeypatch,
    provider,
    mock_settings,
):

    mock_client = MockAsyncClient()

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: mock_client,
    )

    await provider.generate(
        system_prompt="System",
        user_prompt="User",
        temperature=None,
        max_tokens=None,
    )

    payload = mock_client.post_kwargs["json"]

    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 500


@pytest.mark.asyncio
async def test_generate_fails_when_choices_are_missing(
    monkeypatch,
    provider,
    mock_settings,
):

    class EmptyChoicesClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            return MockResponse(
                {
                    "choices": []
                }
            )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: EmptyChoicesClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="No AI response received.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_fails_when_message_is_missing(
    monkeypatch,
    provider,
    mock_settings,
):

    class MissingMessageClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            return MockResponse(
                {
                    "choices": [
                        {}
                    ]
                }
            )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: MissingMessageClient(),
    )

    with pytest.raises(
        AIProviderError,
        match="AI provider returned an invalid response.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_fails_when_content_is_empty(
    monkeypatch,
    provider,
    mock_settings,
):

    class EmptyContentClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            return MockResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": ""
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: EmptyContentClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="AI returned an empty response.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_timeout(
    monkeypatch,
    provider,
    mock_settings,
):

    class TimeoutClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            raise httpx.TimeoutException(
                "Request timed out."
            )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: TimeoutClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="AI request timed out.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_http_error(
    monkeypatch,
    provider,
    mock_settings,
):

    class HTTPErrorClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            request = httpx.Request(
                "POST",
                "https://ai.example.test/v1/chat/completions",
            )

            response = httpx.Response(
                401,
                request=request,
            )

            raise httpx.HTTPStatusError(
                "Unauthorized",
                request=request,
                response=response,
            )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: HTTPErrorClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="AI provider returned HTTP 401.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_request_error(
    monkeypatch,
    provider,
    mock_settings,
):

    class RequestErrorClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            request = httpx.Request(
                "POST",
                "https://ai.example.test/v1/chat/completions",
            )

            raise httpx.RequestError(
                "Connection failed",
                request=request,
            )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: RequestErrorClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="Unable to connect to AI provider.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_invalid_json(
    monkeypatch,
    provider,
    mock_settings,
):

    class InvalidJSONClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            class InvalidJSONResponse(MockResponse):

                def json(self):

                    raise ValueError(
                        "Invalid JSON"
                    )

            return InvalidJSONResponse({})

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: InvalidJSONClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="AI provider returned invalid JSON.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_rejects_non_object_response(
    monkeypatch,
    provider,
    mock_settings,
):

    class ListResponseClient(MockAsyncClient):

        async def post(
            self,
            *args,
            **kwargs,
        ):

            return MockResponse([])

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        lambda *args, **kwargs: ListResponseClient(),
    )

    with pytest.raises(
        AIProviderError,
        match="AI provider returned an invalid response.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_configures_http_client(
    monkeypatch,
    provider,
    mock_settings,
):

    captured = {}

    class InspectClient(MockAsyncClient):

        def __init__(
            self,
            *args,
            **kwargs,
        ):

            captured["kwargs"] = kwargs

        async def post(
            self,
            *args,
            **kwargs,
        ):

            return MockResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Response"
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.httpx.AsyncClient",
        InspectClient,
    )

    await provider.generate(
        system_prompt="System",
        user_prompt="User",
    )

    assert captured["kwargs"]["timeout"] == 30.0

    limits = captured["kwargs"]["limits"]

    assert limits.max_connections == 10
    assert limits.max_keepalive_connections == 5


@pytest.mark.asyncio
async def test_generate_rejects_blank_configuration(
    provider,
    mock_settings,
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_API_KEY",
        SecretStr("   "),
    )

    with pytest.raises(
        RuntimeError,
        match="AI configuration is incomplete: AI_API_KEY.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )


@pytest.mark.asyncio
async def test_generate_rejects_invalid_api_url(
    provider,
    mock_settings,
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.ai_engine.providers.ai_provider.settings.AI_API_URL",
        "ai.example.test/v1/chat/completions",
    )

    with pytest.raises(
        RuntimeError,
        match="AI_API_URL must be a full http\\(s\\) URL.",
    ):

        await provider.generate(
            system_prompt="System",
            user_prompt="User",
        )
