import re

from app.models.schemas import Candidate, CandidateSeed, SearchCriteria

MAX_RESULTS = 8
MIN_SCORE = 20

ROLE_EQUIVALENTS: dict[str, set[str]] = {
    "product manager": {"product lead"},
    "product lead": {"product manager"},
    "data scientist": {"data science manager"},
}

TOPIC_LABELS = {
    "ai": "AI",
    "machine learning": "machine learning",
    "product management": "product management",
    "data science": "data science",
    "fintech": "fintech",
    "payments": "payments",
    "developer tools": "developer tools",
    "healthcare": "healthcare",
    "engineering": "engineering",
    "logistics": "logistics",
}


def rank_candidates(
    seeds: list[CandidateSeed],
    criteria: SearchCriteria,
    limit: int = MAX_RESULTS,
) -> list[Candidate]:
    ranked: list[Candidate] = []
    for seed in seeds:
        score, reasons = _score(seed, criteria)
        if score < MIN_SCORE:
            continue
        ranked.append(
            Candidate(
                id=seed.id,
                name=seed.name,
                role=seed.role,
                company=seed.company,
                relevant_experience=seed.relevant_experience,
                match_score=min(score, 100),
                match_reasons=reasons,
                source_urls=list(seed.source_urls),
                linkedin_url=seed.linkedin_url,
            )
        )
    ranked.sort(key=lambda candidate: (-candidate.match_score, candidate.name))
    return ranked[:limit]


def _score(seed: CandidateSeed, criteria: SearchCriteria) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    role_points, role_reason = _role_reason(seed, criteria.target_roles)
    score += role_points
    if role_reason:
        reasons.append(role_reason)

    company_points, company_reason = _company_reason(seed, criteria.target_companies)
    score += company_points
    if company_reason:
        reasons.append(company_reason)

    overlap = [topic for topic in criteria.topics if topic in seed.focus_areas]
    if overlap:
        score += min(30, 10 * len(overlap))
        labels = [TOPIC_LABELS.get(topic, topic) for topic in overlap]
        reasons.append(
            f"Profile details mention { _join(labels) }, which overlaps your request."
        )

    if _transition_matches(seed, criteria):
        score += 15
        reasons.append(
            "Experience describes a move from "
            f"{seed.transition_from} toward {seed.transition_to}, "
            "which matches your stated transition."
        )

    interest_reason = _interest_reason(seed, criteria.interests, overlap)
    if interest_reason:
        score += 8
        reasons.append(interest_reason)

    if not reasons:
        reasons.append("Not enough overlapping evidence to explain a stronger match.")

    return min(score, 100), reasons


def _role_reason(seed: CandidateSeed, target_roles: list[str]) -> tuple[int, str | None]:
    if not target_roles:
        return 10, None

    tags = {tag.casefold() for tag in seed.role_tags}
    for role in target_roles:
        if role.casefold() in tags:
            return 40, f"Listed role '{seed.role}' matches your target role {role}."
        equivalents = {item.casefold() for item in ROLE_EQUIVALENTS.get(role.casefold(), set())}
        if tags & equivalents:
            return (
                32,
                f"Listed role '{seed.role}' is close to your target role {role}.",
            )
    requested = _join(target_roles)
    return 0, f"Listed role '{seed.role}' does not match the requested role ({requested})."


def _company_reason(seed: CandidateSeed, companies: list[str]) -> tuple[int, str | None]:
    if not companies:
        return 5, None
    for company in companies:
        if company.casefold() == seed.company.casefold():
            return 25, f"Company matches your target: {seed.company}."
    requested = _join(companies)
    return (
        0,
        f"No source for this profile confirms a current role at {requested}.",
    )


def _transition_matches(seed: CandidateSeed, criteria: SearchCriteria) -> bool:
    return _aligns(seed.transition_from, criteria.transition_from) and _aligns(
        seed.transition_to, criteria.transition_to
    )


def _aligns(value: str | None, target: str | None) -> bool:
    if not value or not target:
        return False
    return value.casefold() in target.casefold() or target.casefold() in value.casefold()


def _interest_reason(
    seed: CandidateSeed,
    interests: list[str],
    matched_topics: list[str],
) -> str | None:
    haystack = f"{seed.relevant_experience} {' '.join(seed.focus_areas)}"
    for interest in interests:
        key = interest.casefold()
        if _already_covered(key, matched_topics):
            continue
        if _mentioned(key, haystack):
            return f"Profile details mention {interest}, which you listed as an interest."
    return None


def _already_covered(interest: str, topics: list[str]) -> bool:
    for topic in topics:
        label = TOPIC_LABELS.get(topic, topic).casefold()
        if interest == topic or interest == label or interest in topic or topic in interest:
            return True
    return False


def _mentioned(needle: str, haystack: str) -> bool:
    if len(needle) <= 3:
        return re.search(rf"\b{re.escape(needle)}\b", haystack, flags=re.IGNORECASE) is not None
    return needle in haystack.casefold()


def _join(values: list[str]) -> str:
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"
