import httpx

from app.core.config import settings
from app.modules.ai_engine.providers.base import BaseAIProvider


class AIProviderError(RuntimeError):
    """
    Raised when the AI provider cannot return a usable response.
    """


import logging

logger = logging.getLogger(__name__)

class AIProvider(BaseAIProvider):

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:

        api_url, api_key, model = self._get_configuration()

        temperature = (
            settings.AI_TEMPERATURE
            if temperature is None
            else temperature
        )

        max_tokens = (
            settings.AI_MAX_TOKENS
            if max_tokens is None
            else max_tokens
        )

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FarmMateAI/1.0",
        }

        limits = httpx.Limits(
            max_connections=10,
            max_keepalive_connections=5,
        )

        try:

            async with httpx.AsyncClient(
                timeout=settings.AI_REQUEST_TIMEOUT,
                limits=limits,
            ) as client:

                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()

        except httpx.TimeoutException as exc:

            raise AIProviderError(
                "AI request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            logger.error(
                "AI provider returned HTTP %s",
                exc.response.status_code,
            )
            raise AIProviderError(
                f"AI provider returned HTTP "
                f"{exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:

            raise AIProviderError(
                "Unable to connect to AI provider."
            ) from exc

        except ValueError as exc:

            raise AIProviderError(
                "AI provider returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):

            raise AIProviderError(
                "AI provider returned an invalid response."
            )

        choices = data.get("choices")

        if not isinstance(choices, list) or not choices:

            raise AIProviderError(
                "No AI response received."
            )

        first_choice = choices[0]

        if not isinstance(first_choice, dict):

            raise AIProviderError(
                "AI provider returned an invalid response."
            )

        message = first_choice.get("message")

        if not isinstance(message, dict):

            raise AIProviderError(
                "AI provider returned an invalid response."
            )

        content = message.get("content")

        if not isinstance(content, str) or not content.strip():

            raise AIProviderError(
                "AI returned an empty response."
            )

        return content.strip()

    @staticmethod
    def _get_configuration() -> tuple[str, str, str]:

        api_url = settings.AI_API_URL.strip()
        api_key = settings.AI_API_KEY.get_secret_value().strip()
        model = settings.AI_MODEL.strip()

        missing = [
            name
            for name, value in (
                ("AI_API_URL", api_url),
                ("AI_API_KEY", api_key),
                ("AI_MODEL", model),
            )
            if not value
        ]

        if missing:

            raise AIProviderError(
                "AI configuration is incomplete: "
                f"{', '.join(missing)}."
            )

        if not api_url.startswith(
            ("http://", "https://")
        ):

            raise AIProviderError(
                "AI_API_URL must be a full http(s) URL."
            )

        return (
            AIProvider._build_chat_completions_url(api_url),
            api_key,
            model,
        )

    @staticmethod
    def _build_chat_completions_url(api_url: str) -> str:

        base_url = api_url.rstrip("/")

        if base_url.endswith("/chat/completions"):
            return base_url

        return f"{base_url}/chat/completions"
