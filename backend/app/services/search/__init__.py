from app.config import Settings, get_settings
from app.errors import AppError
from app.services.search.base import SearchProvider
from app.services.search.exa import ExaSearchProvider
from app.services.search.mock import MockSearchProvider
from app.services.search.tavily import TavilySearchProvider


def get_search_provider(settings: Settings | None = None) -> SearchProvider:
    settings = settings or get_settings()
    if settings.search_provider == "mock":
        return MockSearchProvider()
    if settings.search_provider == "exa":
        return ExaSearchProvider(api_key=settings.exa_api_key)
    if settings.search_provider == "tavily":
        return TavilySearchProvider(api_key=settings.tavily_api_key)
    raise AppError(
        f"Unknown SEARCH_PROVIDER '{settings.search_provider}'.",
        status_code=500,
    )
