from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse
from app.services.pipeline import run_search

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse, response_model_exclude_none=True)
async def search(request: SearchRequest) -> SearchResponse:
    return await run_search(request)
