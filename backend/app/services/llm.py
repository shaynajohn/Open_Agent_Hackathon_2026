"""OpenAI-compatible chat client.

The search and outreach routes still use local logic. Call `complete` from a
future intent parser, extractor, or outreach writer. Do not send API keys to
the frontend or the extension.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings
from app.errors import AppError

logger = logging.getLogger(__name__)

LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "model-calls.jsonl"
_REJECTED_TOKEN = "rt-local"


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


class ModelCall:
    def __init__(self, requested_model: str, response_model: str | None, text: str) -> None:
        self.requested_model = requested_model
        self.response_model = response_model
        self.text = text


class NightshiftClient(LLMClient):
    """Meterless Nightshift, OpenAI-compatible at http://127.0.0.1:8088/v1."""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str = "http://127.0.0.1:8088/v1",
        app_id: str = "meetmind",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = normalize_nightshift_base(base_url)
        self.app_id = app_id
        self._transport = transport

    async def complete(self, *, system: str, user: str) -> str:
        call = await self.complete_recorded(system=system, user=user)
        return call.text

    async def complete_recorded(self, *, system: str, user: str) -> ModelCall:
        if not self.api_key:
            raise AppError(
                "NIGHTSHIFT_API_KEY is not set. Copy the runtime token into backend/.env. "
                "The placeholder rt-local is rejected.",
                status_code=503,
            )
        if self.api_key.strip().lower() == _REJECTED_TOKEN:
            raise AppError(
                "NIGHTSHIFT_API_KEY is the placeholder rt-local. Paste the token from the Nightshift runtime.",
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
            "meterless-app": self.app_id,
            "meterless-scope": "user",
        }
        try:
            async with httpx.AsyncClient(timeout=180.0, transport=self._transport) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise AppError("Nightshift could not be reached at its /v1 endpoint.", status_code=502) from exc

        if response.status_code in {401, 403}:
            raise AppError("Nightshift rejected the runtime token.", status_code=502)
        if response.status_code >= 400:
            raise AppError("Nightshift request failed.", status_code=502)

        body = response.json()
        content = body.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise AppError("Nightshift returned an empty response.", status_code=502)

        response_model = body.get("model") if isinstance(body.get("model"), str) else None
        header_model = _header_model(response.headers)
        call = ModelCall(
            requested_model=self.model,
            response_model=header_model or response_model,
            text=content.strip(),
        )
        record_model_call(call)
        return call


def normalize_nightshift_base(value: str) -> str:
    """Accept a host, /v1, /v1/chat/completions, /v1/models, or /healthz. Never emit /v1/v1."""
    raw = value.strip()
    if "://" not in raw:
        raw = f"http://{raw}"
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AppError("NIGHTSHIFT_BASE_URL is not a valid HTTP URL.", status_code=503)

    path = parsed.path.rstrip("/")
    for suffix in ("/chat/completions", "/models", "/healthz"):
        if path.endswith(suffix):
            path = path[: -len(suffix)].rstrip("/")
    if path.endswith("/v1/v1"):
        path = path[: -len("/v1")]
    if not path.endswith("/v1"):
        path = f"{path}/v1" if path else "/v1"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def record_model_call(call: ModelCall) -> None:
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "provider": "nightshift",
        "requested_model": call.requested_model,
        "response_model": call.response_model,
    }
    logger.info(
        "nightshift requested_model=%s response_model=%s",
        call.requested_model,
        call.response_model,
    )
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _header_model(headers: httpx.Headers) -> str | None:
    for name in ("meterless-model", "x-meterless-model", "x-model"):
        value = headers.get(name)
        if value:
            return value
    return None


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    if settings.llm_provider == "mock":
        return UnavailableLLMClient()
    if settings.llm_provider == "nightshift":
        return NightshiftClient(
            api_key=settings.nightshift_api_key,
            model=settings.nightshift_model,
            base_url=settings.nightshift_base_url,
            app_id=settings.meterless_app,
        )
    return OpenAIChatClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
    )
