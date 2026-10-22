import logging

import httpx

from app.errors import AppError
from app.models.schemas import SearchCriteria
from app.services.search.base import EXCLUDED_DOMAINS, SearchDocument, build_public_search_query
from app.services.search.exa import _post_json

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class TavilySearchProvider:
    """Search public pages with Tavily. LinkedIn domains are excluded."""

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
                "TAVILY_API_KEY is not set. Use SEARCH_PROVIDER=mock to run without credentials.",
                status_code=503,
            )
        payload = {
            "query": build_public_search_query(criteria),
            "search_depth": "basic",
            "max_results": self.max_results,
            "include_answer": False,
            "exclude_domains": EXCLUDED_DOMAINS,
        }
        body = await _post_json(
            TAVILY_SEARCH_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
            transport=self._transport,
            provider_name="Tavily",
        )
        documents: list[SearchDocument] = []
        for item in body.get("results", []):
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if not isinstance(url, str) or not url:
                continue
            content = item.get("content") if isinstance(item.get("content"), str) else ""
            documents.append(
                SearchDocument(
                    url=url,
                    title=item.get("title") if isinstance(item.get("title"), str) else url,
                    text=content,
                )
            )
        logger.debug("Tavily returned %s documents", len(documents))
        return documents
