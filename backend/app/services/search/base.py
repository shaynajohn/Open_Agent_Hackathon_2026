from typing import Literal, Protocol

from pydantic import BaseModel

from app.models.schemas import SearchCriteria

EXCLUDED_DOMAINS = ["linkedin.com", "www.linkedin.com", "lnkd.in"]


class SearchDocument(BaseModel):
    url: str
    title: str
    text: str = ""
    mock_profile_id: str | None = None


class SearchProvider(Protocol):
    source_kind: Literal["mock", "web"]

    async def search(self, criteria: SearchCriteria) -> list[SearchDocument]:
        """Return public documents. Do not fetch LinkedIn pages."""


def build_public_search_query(criteria: SearchCriteria) -> str:
    """Bias search toward pages we are allowed to read, such as bios and team pages."""
    hints: list[str] = []
    if criteria.target_roles:
        hints.append(criteria.target_roles[0])
    if criteria.target_companies:
        hints.append(criteria.target_companies[0])
    if criteria.topics:
        hints.append(" ".join(criteria.topics[:4]))
    extra = " ".join(hints)
    return (
        f"{criteria.raw_query} {extra} "
        "(conference speaker OR team page OR interview OR biography)"
    ).strip()
