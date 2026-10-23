import json

import httpx
import pytest

from app.config import Settings
from app.errors import AppError
from app.services.llm import NightshiftClient, normalize_nightshift_base
from app.services.zetaris import _query, query_select_one


def test_nightshift_url_never_doubles_the_v1_prefix():
    assert normalize_nightshift_base("127.0.0.1:8088") == "http://127.0.0.1:8088/v1"
    assert normalize_nightshift_base("http://127.0.0.1:8088/v1") == "http://127.0.0.1:8088/v1"
    assert (
        normalize_nightshift_base("http://127.0.0.1:8088/v1/chat/completions")
        == "http://127.0.0.1:8088/v1"
    )
    assert normalize_nightshift_base("http://127.0.0.1:8088/healthz") == "http://127.0.0.1:8088/v1"
    assert normalize_nightshift_base("http://127.0.0.1:8088/v1/v1") == "http://127.0.0.1:8088/v1"


def test_nightshift_rejects_the_placeholder_token():
    client = NightshiftClient(api_key="rt-local", model="meterless/auto")

    with pytest.raises(AppError, match="rt-local"):
        import asyncio

        asyncio.run(client.complete_recorded(system="Be brief.", user="Say ready."))


def test_nightshift_records_the_model_id(tmp_path, monkeypatch):
    import asyncio

    monkeypatch.setattr("app.services.llm.LOG_PATH", tmp_path / "model-calls.jsonl")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content.decode())
        captured["app"] = request.headers["meterless-app"]
        captured["scope"] = request.headers["meterless-scope"]
        return httpx.Response(
            200,
            headers={"meterless-model": "nvidia/nemotron"},
            json={"model": "meterless/auto", "choices": [{"message": {"content": "ready"}}]},
        )

    client = NightshiftClient(
        api_key="runtime-token",
        model="meterless/auto",
        transport=httpx.MockTransport(handler),
    )
    call = asyncio.run(client.complete_recorded(system="Be brief.", user="Say ready."))

    assert call.text == "ready"
    assert call.requested_model == "meterless/auto"
    assert call.response_model == "nvidia/nemotron"
    assert captured["body"]["model"] == "meterless/auto"
    assert captured["url"].endswith("/v1/chat/completions")
    assert captured["app"] == "meetmind"
    logged = json.loads((tmp_path / "model-calls.jsonl").read_text().strip())
    assert logged["response_model"] == "nvidia/nemotron"
    assert "runtime-token" not in (tmp_path / "model-calls.jsonl").read_text()


def test_integration_status_reports_missing_credentials(client):
    response = client.get("/api/integrations")

    assert response.status_code == 200
    body = response.json()
    assert body["zetaris"]["ok"] is False
    assert body["nightshift"]["ok"] is False
    assert "ZETARIS_API_KEY" in body["zetaris"]["detail"]
    assert "NIGHTSHIFT_API_KEY" in body["nightshift"]["detail"]


def test_zetaris_select_one_uses_the_direct_rest_contract():
    import asyncio

    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content.decode())
        captured["org"] = request.headers["x-org-id"]
        captured["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"data": [["1"]]})

    settings = Settings(
        zetaris_rest_url="https://cluster.example/api/v1.0",
        zetaris_org_id="7",
        zetaris_api_key="zetaris-key",
    )
    result = asyncio.run(
        query_select_one(settings, transport=httpx.MockTransport(handler))
    )

    assert result.rows == [["1"]]
    assert result.route == "rest"
    assert captured["url"] == "https://cluster.example/api/v1.0/sql-editor/sqls/run"
    assert captured["body"]["sql"] == "SELECT 1"
    assert captured["body"]["source"] == "SqlEditor"
    assert captured["org"] == "7"
    assert captured["auth"] == "Bearer zetaris-key"


def test_zetaris_uses_the_gateway_when_only_the_sign_in_origin_is_set():
    import asyncio

    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"data": [["1"]]})

    settings = Settings(
        zetaris_rest_url="http://localhost:8888/api/v1.0",
        zetaris_base_url="https://gateway.example",
        zetaris_org_id="7",
        zetaris_api_key="zetaris-key",
    )
    result = asyncio.run(
        query_select_one(settings, transport=httpx.MockTransport(handler))
    )

    assert result.route == "gateway"
    assert captured["url"] == "https://gateway.example/api/proxy/sql-editor/sqls/run-query"


def test_zetaris_refuses_sql_other_than_select_one():
    import asyncio

    settings = Settings(
        zetaris_rest_url="https://cluster.example/api/v1.0",
        zetaris_org_id="7",
        zetaris_api_key="zetaris-key",
    )

    with pytest.raises(AppError, match="SELECT 1"):
        asyncio.run(_query("DROP TABLE people", settings=settings))
