import logging

from app.fixtures.mock_profiles import PROFILES_BY_ID
from app.models.schemas import CandidateSeed
from app.services.search.base import SearchDocument

logger = logging.getLogger(__name__)


def extract_candidates(documents: list[SearchDocument]) -> list[CandidateSeed]:
    """Turn retrieved documents into profiles.

    Mock documents carry a fixture id. Unstructured web text is ignored so the
    scaffold never invents a name, role, or employer from a page snippet.
    An LLM extractor can replace this function later and should refuse fields
    it cannot support with a source URL.
    """
    seeds: list[CandidateSeed] = []
    for document in documents:
        if not document.mock_profile_id:
            continue
        profile = PROFILES_BY_ID.get(document.mock_profile_id)
        if profile is None:
            logger.warning("Ignoring unknown mock profile id %s", document.mock_profile_id)
            continue
        seeds.append(profile)
    return seeds


def dedupe_candidates(seeds: list[CandidateSeed]) -> list[CandidateSeed]:
    seen: set[tuple[str, str]] = set()
    unique: list[CandidateSeed] = []
    for seed in seeds:
        key = (seed.name.casefold().strip(), seed.company.casefold().strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(seed)
    return unique
