"""音声文字起こしエンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from .. import schemas
from ..services import transcription as tsvc

router = APIRouter(prefix="/api/transcribe", tags=["transcription"])


@router.post("", response_model=schemas.TranscriptionResponse)
async def transcribe(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="音声データが空です")
    try:
        text = await tsvc.transcribe(
            data, file.filename or "audio.webm", file.content_type
        )
    except tsvc.TranscriptionNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schemas.TranscriptionResponse(text=text)
