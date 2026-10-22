from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

MOCK_DISCLAIMER = (
    "Match scores are estimates for ranking, not objective facts. "
    "These profiles are fictional sample data for local development. "
    "They were not found on the web, and the source URLs are placeholders. "
    "Do not treat them as real people."
)

WEB_DISCLAIMER = (
    "Match scores are estimates for ranking, not objective facts. "
    "Only details supported by the retrieved public sources should be trusted. "
    "Missing fields are left blank instead of being guessed."
)

WEB_AWAITING_EXTRACTION_DISCLAIMER = (
    "Match scores are estimates for ranking, not objective facts. "
    "Public pages were retrieved, but turning those pages into candidate profiles "
    "is not implemented yet. No people were inferred from unstructured text. "
    "Use SEARCH_PROVIDER=mock to demo the interface with sample profiles."
)


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _require_http_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be an absolute http(s) URL")
    return value.strip()


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural-language networking goal.",
    )
    background: str | None = Field(
        None,
        max_length=2000,
        description="Optional context about the user's experience.",
    )
    interests: str | None = Field(
        None,
        max_length=1000,
        description="Optional interests, separated by commas.",
    )

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("Query must be at least 3 characters.")
        return stripped

    @field_validator("background", "interests")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return _clean_optional(value)


class SearchCriteria(BaseModel):
    """Structured reading of a networking request. Fields can be incomplete."""

    raw_query: str
    target_roles: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    background: str | None = None
    interests: list[str] = Field(default_factory=list)
    transition_from: str | None = None
    transition_to: str | None = None


class CandidateSeed(BaseModel):
    """Internal profile used before scoring. Not returned by the API."""

    id: str
    name: str
    role: str
    company: str
    relevant_experience: str
    role_tags: list[str]
    focus_areas: list[str]
    source_urls: list[str]
    linkedin_url: str | None = None
    transition_from: str | None = None
    transition_to: str | None = None


class Candidate(BaseModel):
    id: str
    name: str
    role: str
    company: str
    relevant_experience: str
    match_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Estimated alignment from 0 to 100. This is a ranking aid, not a measurement.",
    )
    match_reasons: list[str] = Field(
        ...,
        min_length=1,
        description="Explainable reasons grounded in the profile details that were actually retrieved.",
    )
    source_urls: list[str] = Field(default_factory=list)
    linkedin_url: str | None = Field(
        None,
        description=(
            "Present only when the URL was verified from a permitted public source. "
            "Do not populate this by scraping LinkedIn."
        ),
    )
    outreach_draft: str | None = None

    @field_validator("source_urls")
    @classmethod
    def validate_source_urls(cls, value: list[str]) -> list[str]:
        return [_require_http_url(url) for url in value]

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _require_http_url(value)


class SearchResponse(BaseModel):
    query: str
    criteria: SearchCriteria
    candidates: list[Candidate]
    result_source: Literal["mock", "web"]
    sources_retrieved: int = Field(
        ...,
        ge=0,
        description="Documents returned by the search provider before ranking.",
    )
    disclaimer: str


class OutreachRequest(BaseModel):
    candidate: Candidate
    query: str = Field(..., min_length=3, max_length=2000)
    background: str | None = Field(None, max_length=2000)
    interests: str | None = Field(None, max_length=1000)
    tone: Literal["warm", "direct", "curious"] = "warm"

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("Query must be at least 3 characters.")
        return stripped

    @field_validator("background", "interests")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return _clean_optional(value)


class OutreachResponse(BaseModel):
    candidate_name: str
    subject: str
    message: str
    result_source: Literal["mock", "llm"]
    disclaimer: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
