"""OpenAI-compatible chat client.

The search and outreach routes still use local logic. Call `complete` from a
future intent parser, extractor, or outreach writer. Do not send API keys to
the frontend or the extension.
"""

import httpx

from app.config import Settings, get_settings
from app.errors import AppError


class LLMClient:
    async def complete(self, *, system: str, user: str) -> str:
        raise NotImplementedError


class UnavailableLLMClient(LLMClient):
    async def complete(self, *, system: str, user: str) -> str:
        raise AppError(
            "LLM_PROVIDER is mock. Intent parsing and outreach currently use local logic.",
            status_code=503,
        )


class OpenAIChatClient(LLMClient):
    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._transport = transport

    async def complete(self, *, system: str, user: str) -> str:
        if not self.api_key:
            raise AppError(
                "OPENAI_API_KEY is not set. Keep LLM_PROVIDER=mock to run without credentials.",
                status_code=503,
            )
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0, transport=self._transport) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise AppError("The language model could not be reached.", status_code=502) from exc

        if response.status_code in {401, 403}:
            raise AppError("The language model rejected the API key.", status_code=502)
        if response.status_code >= 400:
            raise AppError("The language model request failed.", status_code=502)

        content = response.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise AppError("The language model returned an empty response.", status_code=502)
        return content.strip()


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    if settings.llm_provider == "mock":
        return UnavailableLLMClient()
    return OpenAIChatClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
    )
