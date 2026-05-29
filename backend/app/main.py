"""FastAPI エントリポイント。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import schemas
from .config import get_settings
from .database import init_db
from .routers import (
    chat,
    conversations,
    memories,
    research,
    transcription,
    users,
)
from .services import llm
from .services import search as search_svc
from .services import transcription as tsvc

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(memories.router)
app.include_router(research.router)
app.include_router(transcription.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config", response_model=schemas.ConfigOut)
def get_config():
    """フロントへ公開する設定・機能の有効状態。"""
    return schemas.ConfigOut(
        app_name=settings.app_name,
        owner_name=settings.owner_name,
        chat_model=settings.chat_model,
        embedding_provider=settings.resolved_embedding_provider,
        search_enabled=search_svc.is_enabled(),
        transcription_enabled=tsvc.is_enabled(),
        llm_enabled=llm.is_enabled(),
    )
