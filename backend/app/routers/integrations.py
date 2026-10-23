from fastapi import APIRouter

from app.config import Settings, get_settings
from app.errors import AppError
from app.services.llm import NightshiftClient
from app.services.zetaris import query_select_one

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/")
async def integration_status() -> dict[str, object]:
    """Check Zetaris with SELECT 1 and Nightshift with one short completion."""
    settings = get_settings()
    return {
        "zetaris": await _zetaris(settings),
        "nightshift": await _nightshift(settings),
    }


async def _zetaris(settings: Settings) -> dict[str, object]:
    try:
        result = await query_select_one(settings)
    except AppError as exc:
        return {"ok": False, "detail": exc.message}
    value = result.rows[0][0] if result.rows and result.rows[0] else None
    return {
        "ok": str(value) == "1",
        "route": result.route,
        "rows": result.rows,
    }


async def _nightshift(settings: Settings) -> dict[str, object]:
    try:
        client = NightshiftClient(
            api_key=settings.nightshift_api_key,
            model=settings.nightshift_model,
            base_url=settings.nightshift_base_url,
            app_id=settings.meterless_app,
        )
        call = await client.complete_recorded(
            system="You are MeetMind. Reply with one short sentence.",
            user="Reply with the single word ready.",
        )
    except AppError as exc:
        return {"ok": False, "detail": exc.message}
    return {
        "ok": True,
        "text": call.text,
        "requested_model": call.requested_model,
        "response_model": call.response_model,
    }
