import pytest
from pydantic import ValidationError

from app.models.schemas import Candidate, OutreachRequest, SearchRequest


def test_search_request_strips_query_and_rejects_short_text():
    request = SearchRequest(query="  meet a product manager  ", background="  ", interests=None)

    assert request.query == "meet a product manager"
    assert request.background is None

    with pytest.raises(ValidationError):
        SearchRequest(query="hi")


def test_candidate_score_must_stay_in_range():
    payload = {
        "id": "person",
        "name": "Ada Example",
        "role": "Product Manager",
        "company": "Example Co",
        "relevant_experience": "Ships AI features.",
        "match_score": 101,
        "match_reasons": ["Role overlaps."],
        "source_urls": ["https://example.com/ada"],
    }

    with pytest.raises(ValidationError):
        Candidate(**payload)


def test_candidate_linkedin_url_is_optional_and_must_be_absolute():
    candidate = Candidate(
        id="person",
        name="Ada Example",
        role="Product Manager",
        company="Example Co",
        relevant_experience="Ships AI features.",
        match_score=70,
        match_reasons=["Role overlaps."],
        source_urls=["https://example.com/ada"],
    )

    assert candidate.linkedin_url is None

    with pytest.raises(ValidationError):
        Candidate.model_validate({**candidate.model_dump(), "linkedin_url": "linkedin.com/in/ada"})


def test_outreach_request_requires_a_candidate_and_a_query():
    with pytest.raises(ValidationError):
        OutreachRequest.model_validate({"query": "meet someone in product"})
