import logging

from app.config import Settings, get_settings
from app.models.schemas import (
    MOCK_DISCLAIMER,
    WEB_AWAITING_EXTRACTION_DISCLAIMER,
    WEB_DISCLAIMER,
    SearchRequest,
    SearchResponse,
)
from app.services.extraction import dedupe_candidates, extract_candidates
from app.services.intent import parse_intent
from app.services.ranking import rank_candidates
from app.services.search import get_search_provider

logger = logging.getLogger(__name__)


async def run_search(
    request: SearchRequest,
    settings: Settings | None = None,
) -> SearchResponse:
    settings = settings or get_settings()
    criteria = parse_intent(request)
    provider = get_search_provider(settings)
    documents = await provider.search(criteria)
    seeds = dedupe_candidates(extract_candidates(documents))
    candidates = rank_candidates(seeds, criteria)

    if provider.source_kind == "mock":
        disclaimer = MOCK_DISCLAIMER
    elif candidates:
        disclaimer = WEB_DISCLAIMER
    else:
        disclaimer = WEB_AWAITING_EXTRACTION_DISCLAIMER

    logger.info(
        "search provider=%s documents=%s candidates=%s",
        provider.source_kind,
        len(documents),
        len(candidates),
    )
    return SearchResponse(
        query=request.query,
        criteria=criteria,
        candidates=candidates,
        result_source=provider.source_kind,
        sources_retrieved=len(documents),
        disclaimer=disclaimer,
    )
