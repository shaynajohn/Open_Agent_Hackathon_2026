from app.models.schemas import CandidateSeed, SearchCriteria, SearchRequest
from app.services.extraction import dedupe_candidates, extract_candidates
from app.services.intent import parse_intent
from app.services.ranking import rank_candidates
from app.services.search.base import SearchDocument

EXAMPLE_QUERY = (
    "I want to meet a Product Manager at Stripe who works on AI products. "
    "I'm interested in transitioning from data science into product management."
)


def test_search_returns_ranked_sample_candidates(client):
    response = client.post(
        "/api/search",
        json={
            "query": EXAMPLE_QUERY,
            "background": "I am a data scientist on a growth team.",
            "interests": "AI, clinic scheduling",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result_source"] == "mock"
    assert body["sources_retrieved"] == 8
    assert "fictional" in body["disclaimer"].lower()
    assert 5 <= len(body["candidates"]) <= 10

    criteria = body["criteria"]
    assert "product manager" in criteria["target_roles"]
    assert "Stripe" in criteria["target_companies"]
    assert {"ai", "data science", "product management"} <= set(criteria["topics"])
    assert criteria["transition_from"] == "data science"
    assert criteria["transition_to"] == "product management"

    scores = [candidate["match_score"] for candidate in body["candidates"]]
    assert scores == sorted(scores, reverse=True)
    assert body["candidates"][0]["name"] == "Jordan Hale"

    for candidate in body["candidates"]:
        assert candidate["company"] != "Stripe"
        assert "linkedin_url" not in candidate
        assert candidate["source_urls"]
        assert 0 <= candidate["match_score"] <= 100
        assert any("Stripe" in reason for reason in candidate["match_reasons"])


def test_search_rejects_a_too_short_query(client):
    response = client.post("/api/search", json={"query": "hi"})

    assert response.status_code == 422


def test_interests_can_change_rank_order():
    criteria = parse_intent(
        SearchRequest(query=EXAMPLE_QUERY, interests="clinic scheduling")
    )
    from app.fixtures.mock_profiles import MOCK_PROFILES

    ranked = rank_candidates(MOCK_PROFILES, criteria)
    names = [candidate.name for candidate in ranked]

    assert names.index("Elena Vasquez") < names.index("Maya Chen")


def test_extraction_does_not_invent_people_from_unstructured_text():
    documents = [
        SearchDocument(
            url="https://example.com/team",
            title="Team",
            text="Jane Doe is a product manager at Stripe and works on AI.",
        )
    ]

    assert extract_candidates(documents) == []


def test_dedupe_keeps_the_first_profile_for_the_same_person():
    seed = CandidateSeed(
        id="one",
        name="Jordan Hale",
        role="Product Manager",
        company="Northstar Analytics",
        relevant_experience="First bio.",
        role_tags=["product manager"],
        focus_areas=["ai"],
        source_urls=["https://example.com/one"],
    )
    duplicate = seed.model_copy(update={"id": "two", "relevant_experience": "Second bio."})

    assert dedupe_candidates([seed, duplicate]) == [seed]


def test_low_overlap_queries_do_not_pad_results(client):
    response = client.post(
        "/api/search",
        json={"query": "I want to meet a recruiter at a hospital."},
    )

    assert response.status_code == 200
    assert response.json()["candidates"] == []
