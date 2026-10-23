"""Read-only Zetaris client.

Direct REST matches the getting-started preflight: POST
`{ZETARIS_REST_URL}/sql-editor/sqls/run`. On an AWS cluster that URL is the
cluster API base ending in `/api/v1.0`, not localhost. If only the Gateway
sign-in origin is available, set `ZETARIS_BASE_URL` and leave the REST URL
pointing at a host you cannot reach; the probe uses the UI proxy when the
direct API is unset.
"""

import re
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings
from app.errors import AppError

_SELECT_ONE = re.compile(r"^\s*select\s+1(\s+as\s+[A-Za-z_][A-Za-z0-9_]*)?\s*$", re.I)


class ZetarisResult:
    def __init__(self, rows: list[list[Any]], route: str) -> None:
        self.rows = rows
        self.route = route


async def query_select_one(
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ZetarisResult:
    """Run the fixed statement SELECT 1. Other SQL is refused."""
    return await _query("SELECT 1", settings=settings, transport=transport)


async def _query(
    sql: str,
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ZetarisResult:
    if _SELECT_ONE.match(sql) is None:
        raise AppError("This check only runs SELECT 1.", status_code=400)

    settings = settings or get_settings()
    if not settings.zetaris_api_key or not settings.zetaris_org_id:
        raise AppError(
            "Set ZETARIS_API_KEY and ZETARIS_ORG_ID in backend/.env. "
            "Create the key in the Zetaris Gateway under Management → API Tokens.",
            status_code=503,
        )
    if not settings.zetaris_org_id.isdigit():
        raise AppError("ZETARIS_ORG_ID must be the numeric organisation ID.", status_code=503)

    if _rest_is_configured(settings):
        return await _direct_rest(sql, settings, transport)
    if settings.zetaris_base_url:
        return await _ui_proxy(sql, settings, transport)
    raise AppError(
        "Set ZETARIS_REST_URL to the cluster API base ending in /api/v1.0, "
        "or ZETARIS_BASE_URL to the Gateway sign-in origin.",
        status_code=503,
    )


def _rest_is_configured(settings: Settings) -> bool:
    """Localhost:8888 is the Docker default. An AWS cluster must replace it."""
    url = (settings.zetaris_rest_url or "").strip()
    if not url:
        return False
    if settings.zetaris_base_url and _is_local_default(url):
        return False
    return True


def _is_local_default(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port == 8888


async def _direct_rest(
    sql: str,
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None,
) -> ZetarisResult:
    base = settings.zetaris_rest_url.rstrip("/")
    payload = {
        "queryId": str(uuid.uuid4()),
        "sql": sql,
        "source": "SqlEditor",
        "limit": 1,
    }
    body = await _post(
        f"{base}/sql-editor/sqls/run",
        payload,
        settings,
        transport,
        "Zetaris",
    )
    rows = body.get("data") if isinstance(body, dict) else None
    return ZetarisResult(rows if isinstance(rows, list) else [], "rest")


async def _ui_proxy(
    sql: str,
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None,
) -> ZetarisResult:
    origin = _ui_origin(settings.zetaris_base_url or "")
    body = await _post(
        f"{origin}/api/proxy/sql-editor/sqls/run-query",
        {"sql": sql, "limit": 1},
        settings,
        transport,
        "Zetaris Gateway",
    )
    rows = _rows_from_proxy(body)
    return ZetarisResult(rows, "gateway")


def _ui_origin(value: str) -> str:
    raw = value.strip().rstrip("/")
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path not in {"", "/"}:
        raise AppError(
            "ZETARIS_BASE_URL must be the Gateway origin with no path, such as https://your-cluster.example.",
            status_code=503,
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def _rows_from_proxy(body: object) -> list[list[Any]]:
    if not isinstance(body, dict):
        return []
    data = body.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    return []


async def _post(
    url: str,
    payload: dict[str, object],
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None,
    name: str,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {settings.zetaris_api_key}",
        "X-Org-ID": settings.zetaris_org_id or "",
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=60.0, transport=transport) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise AppError(f"{name} could not be reached.", status_code=502) from exc

    if response.status_code in {401, 403}:
        raise AppError(f"{name} rejected the API key.", status_code=502)
    if response.status_code >= 400:
        raise AppError(f"{name} query failed ({response.status_code}).", status_code=502)

    body = response.json()
    if not isinstance(body, dict):
        raise AppError(f"{name} returned an unexpected response.", status_code=502)
    return body
