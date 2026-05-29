"""音声文字起こし（OpenAI Whisper API / ローカル faster-whisper）。"""

from __future__ import annotations

import asyncio
import os
import tempfile

import httpx

from ..config import get_settings

settings = get_settings()

_TIMEOUT = httpx.Timeout(120.0)


class TranscriptionNotConfigured(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "文字起こしが未設定です。OPENAI_API_KEY を設定するか、"
            "TRANSCRIPTION_PROVIDER=faster-whisper を使ってください。"
        )


def is_enabled() -> bool:
    if settings.transcription_provider == "faster-whisper":
        return True  # ローカル実行（パッケージ未導入なら実行時にエラー）
    return bool(settings.openai_api_key)


async def transcribe(
    data: bytes, filename: str, content_type: str | None = None
) -> str:
    if settings.transcription_provider == "faster-whisper":
        return await asyncio.to_thread(_faster_whisper, data, filename)
    return await _openai_whisper(data, filename, content_type)


async def _openai_whisper(
    data: bytes, filename: str, content_type: str | None
) -> str:
    if not settings.openai_api_key:
        raise TranscriptionNotConfigured()
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            data={"model": settings.whisper_model},
            files={
                "file": (
                    filename or "audio.webm",
                    data,
                    content_type or "application/octet-stream",
                )
            },
        )
        resp.raise_for_status()
        return resp.json().get("text", "")


_fw_model = None


def _faster_whisper(data: bytes, filename: str) -> str:
    global _fw_model
    from faster_whisper import WhisperModel  # 遅延 import（重いため）

    if _fw_model is None:
        _fw_model = WhisperModel(settings.faster_whisper_model)

    suffix = os.path.splitext(filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = f.name
    try:
        segments, _info = _fw_model.transcribe(path)
        return "".join(seg.text for seg in segments).strip()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
