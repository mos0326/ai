"""リサーチエンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import schemas
from ..services import research as research_svc
from ..services.search import SearchNotConfigured

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("", response_model=schemas.ResearchResponse)
async def run_research(payload: schemas.ResearchRequest):
    try:
        result = await research_svc.run_research(
            payload.query, include_images=payload.include_images
        )
    except SearchNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
