from fastapi import APIRouter

from app.models.schemas import OutreachRequest, OutreachResponse
from app.services.outreach import generate_outreach

router = APIRouter(tags=["outreach"])


@router.post("/outreach", response_model=OutreachResponse)
async def outreach(request: OutreachRequest) -> OutreachResponse:
    return generate_outreach(request)
