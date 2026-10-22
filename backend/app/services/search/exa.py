import logging

import httpx

from app.errors import AppError
from app.models.schemas import SearchCriteria
from app.services.search.base import EXCLUDED_DOMAINS, SearchDocument, build_public_search_query

logger = logging.getLogger(__name__)

EXA_SEARCH_URL = "https://api.exa.ai/search"


class ExaSearchProvider:
    """Search public pages with Exa. LinkedIn domains are excluded."""

    source_kind = "web"

    def __init__(
        self,
        api_key: str | None,
        transport: httpx.AsyncBaseTransport | None = None,
        max_results: int = 8,
    ) -> None:
        self.api_key = api_key
        self._transport = transport
        self.max_results = max_results

    async def search(self, criteria: SearchCriteria) -> list[SearchDocument]:
        if not self.api_key:
            raise AppError(
                "EXA_API_KEY is not set. Use SEARCH_PROVIDER=mock to run without credentials.",
                status_code=503,
            )
        payload = {
            "query": build_public_search_query(criteria),
            "type": "auto",
            "numResults": self.max_results,
            "excludeDomains": EXCLUDED_DOMAINS,
            "contents": {"highlights": True},
        }
        body = await _post_json(
            EXA_SEARCH_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
            transport=self._transport,
            provider_name="Exa",
        )
        documents: list[SearchDocument] = []
        for item in body.get("results", []):
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if not isinstance(url, str) or not url:
                continue
            highlights = item.get("highlights") or []
            if isinstance(highlights, list):
                text = "\n".join(part for part in highlights if isinstance(part, str))
            else:
                text = ""
            if not text and isinstance(item.get("text"), str):
                text = item["text"]
            documents.append(
                SearchDocument(
                    url=url,
                    title=item.get("title") if isinstance(item.get("title"), str) else url,
                    text=text,
                )
            )
        return documents


async def _post_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict,
    transport: httpx.AsyncBaseTransport | None,
    provider_name: str,
) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20.0, transport=transport) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        logger.warning("%s request failed before a response", provider_name)
        raise AppError(f"{provider_name} could not be reached.", status_code=502) from exc

    if response.status_code in {401, 403}:
        raise AppError(f"{provider_name} rejected the API key.", status_code=502)
    if response.status_code >= 400:
        logger.warning("%s returned status %s", provider_name, response.status_code)
        raise AppError(f"{provider_name} search failed.", status_code=502)

    data = response.json()
    if not isinstance(data, dict):
        raise AppError(f"{provider_name} returned an unexpected response.", status_code=502)
    return data
