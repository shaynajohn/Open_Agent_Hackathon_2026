from app.models.schemas import Candidate


def _candidate() -> dict:
    return Candidate(
        id="jordan-hale",
        name="Jordan Hale",
        role="Product Manager",
        company="Northstar Analytics",
        relevant_experience="Moved from data science into product.",
        match_score=85,
        match_reasons=["Listed role 'Product Manager' matches your target role product manager."],
        source_urls=["https://example.com/meetmind-demo/jordan-hale"],
    ).model_dump()


def test_outreach_uses_only_known_fields(client):
    response = client.post(
        "/api/outreach",
        json={
            "candidate": _candidate(),
            "query": "I want to meet a product manager who moved out of data science.",
            "background": "I am a data scientist exploring product roles.",
            "interests": "AI forecasting",
            "tone": "warm",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result_source"] == "mock"
    assert body["candidate_name"] == "Jordan Hale"
    assert "Northstar Analytics" in body["subject"]
    assert "Hi Jordan" in body["message"]
    assert "data scientist exploring product roles" in body["message"]
    assert "AI forecasting" in body["message"]
    assert "template" in body["disclaimer"].lower()


def test_outreach_rejects_missing_context(client):
    response = client.post("/api/outreach", json={"query": "meet a product manager"})

    assert response.status_code == 422
