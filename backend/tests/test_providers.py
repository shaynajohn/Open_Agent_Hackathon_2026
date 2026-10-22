import asyncio
import json

import httpx
import pytest

from app.errors import AppError
from app.models.schemas import SearchCriteria
from app.services.llm import OpenAIChatClient
from app.services.search.exa import ExaSearchProvider
from app.services.search.tavily import TavilySearchProvider


def _criteria() -> SearchCriteria:
    return SearchCriteria(raw_query="AI product manager at a payments company")


def test_exa_requires_an_api_key():
    provider = ExaSearchProvider(api_key=None)

    with pytest.raises(AppError, match="EXA_API_KEY"):
        asyncio.run(provider.search(_criteria()))


def test_tavily_requires_an_api_key():
    provider = TavilySearchProvider(api_key=None)

    with pytest.raises(AppError, match="TAVILY_API_KEY"):
        asyncio.run(provider.search(_criteria()))


def test_exa_request_excludes_linkedin_and_returns_documents():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        captured["auth"] = request.headers["authorization"]
        captured["url"] = str(request.url)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Conference bio",
                        "url": "https://example.com/speakers/ada",
                        "highlights": ["Ada speaks about AI products."],
                    }
                ]
            },
        )

    provider = ExaSearchProvider(api_key="test-key", transport=httpx.MockTransport(handler))
    documents = asyncio.run(provider.search(_criteria()))

    assert captured["url"] == "https://api.exa.ai/search"
    assert captured["auth"] == "Bearer test-key"
    assert "linkedin.com" in captured["body"]["excludeDomains"]
    assert documents[0].url == "https://example.com/speakers/ada"
    assert documents[0].mock_profile_id is None
    assert "Ada speaks" in documents[0].text


def test_tavily_request_excludes_linkedin():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Team page",
                        "url": "https://example.com/team",
                        "content": "Public team biography.",
                    }
                ]
            },
        )

    provider = TavilySearchProvider(api_key="test-key", transport=httpx.MockTransport(handler))
    documents = asyncio.run(provider.search(_criteria()))

    assert "linkedin.com" in captured["body"]["exclude_domains"]
    assert captured["body"]["include_answer"] is False
    assert documents[0].text == "Public team biography."


def test_openai_client_posts_chat_completion_without_logging_the_key():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers["authorization"]
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  A careful summary.  "}}]},
        )

    client = OpenAIChatClient(
        api_key="sk-test",
        model="gpt-4o-mini",
        transport=httpx.MockTransport(handler),
    )
    text = asyncio.run(client.complete(system="Be careful.", user="Summarize the bio."))

    assert text == "A careful summary."
    assert captured["auth"] == "Bearer sk-test"
    assert captured["body"]["messages"][0]["content"] == "Be careful."
    assert captured["body"]["model"] == "gpt-4o-mini"
