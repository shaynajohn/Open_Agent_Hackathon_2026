import logging
import re

from app.models.schemas import SearchCriteria, SearchRequest

logger = logging.getLogger(__name__)

# Longer patterns are listed first so "product manager" wins over shorter titles.
ROLE_PATTERNS: list[tuple[str, str]] = [
    (r"product managers?", "product manager"),
    (r"product leads?", "product lead"),
    (r"product management", "product manager"),
    (r"data scientists?", "data scientist"),
    (r"engineering managers?", "engineering manager"),
    (r"software engineers?", "software engineer"),
    (r"\bdesigners?\b", "designer"),
    (r"\bfounders?\b", "founder"),
    (r"\brecruiters?\b", "recruiter"),
]

# Multi-word topics are checked before short aliases such as "ai".
TOPIC_PATTERNS: list[tuple[str, str]] = [
    (r"artificial intelligence", "ai"),
    (r"machine learning", "machine learning"),
    (r"product management", "product management"),
    (r"product managers?", "product management"),
    (r"data scientists?", "data science"),
    (r"data science", "data science"),
    (r"developer tools", "developer tools"),
    (r"\bhealthcare\b", "healthcare"),
    (r"\bfintech\b", "fintech"),
    (r"\bpayments?\b", "payments"),
    (r"\bai\b", "ai"),
]

COMPANY_RE = re.compile(
    r"\bat\s+([A-Z][A-Za-z0-9&.'’+-]*(?:\s+[A-Z][A-Za-z0-9&.'’+-]*){0,3})"
)
TRANSITION_RE = re.compile(
    r"\bfrom\s+(.+?)\s+(?:into|to)\s+(.+?)(?:[.!?]|$)",
    re.IGNORECASE,
)
COMPANY_STOPWORDS = {
    "the",
    "a",
    "an",
    "my",
    "our",
    "this",
    "that",
    "some",
}


def parse_intent(request: SearchRequest) -> SearchCriteria:
    """Read roles, companies, and topics with deterministic rules.

    Replace this function with an LLM-backed parser when you want messier
    queries. Keep the SearchCriteria shape so ranking does not need to change.
    """
    combined = "\n".join(
        part for part in (request.query, request.background, request.interests) if part
    )
    transition_from, transition_to = _transition(request.query)
    criteria = SearchCriteria(
        raw_query=request.query,
        target_roles=_roles(request.query),
        target_companies=_companies(request.query),
        topics=_topics(combined),
        background=request.background,
        interests=_interests(request.interests),
        transition_from=transition_from,
        transition_to=transition_to,
    )
    logger.debug(
        "Parsed intent roles=%s companies=%s topics=%s",
        criteria.target_roles,
        criteria.target_companies,
        criteria.topics,
    )
    return criteria


def _roles(text: str) -> list[str]:
    found: list[str] = []
    for pattern, label in ROLE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(label)
    return _unique(found)


def _topics(text: str) -> list[str]:
    found: list[str] = []
    for pattern, label in TOPIC_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(label)
    return _unique(found)


def _companies(text: str) -> list[str]:
    found: list[str] = []
    for match in COMPANY_RE.findall(text):
        company = match.strip(" .,;")
        if company.casefold() in COMPANY_STOPWORDS:
            continue
        found.append(company)
    return _unique(found)


def _interests(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r",|\band\b", value, flags=re.IGNORECASE)
    return _unique([part.strip(" .") for part in parts if part.strip(" .")])


def _transition(text: str) -> tuple[str | None, str | None]:
    match = TRANSITION_RE.search(text)
    if not match:
        return None, None
    start = _clip_phrase(match.group(1))
    end = _clip_phrase(match.group(2))
    if not start or not end:
        return None, None
    return start, end


def _clip_phrase(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" .,:;-")
    return cleaned[:80]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if not value:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique
