import logging

from app.fixtures.mock_profiles import MOCK_PROFILES
from app.models.schemas import SearchCriteria
from app.services.search.base import SearchDocument

logger = logging.getLogger(__name__)


class MockSearchProvider:
    source_kind = "mock"

    async def search(self, criteria: SearchCriteria) -> list[SearchDocument]:
        logger.debug("Returning sample profiles for a query of %s characters", len(criteria.raw_query))
        return [
            SearchDocument(
                url=profile.source_urls[0],
                title=f"{profile.name}, {profile.role} at {profile.company}",
                text=profile.relevant_experience,
                mock_profile_id=profile.id,
            )
            for profile in MOCK_PROFILES
        ]
