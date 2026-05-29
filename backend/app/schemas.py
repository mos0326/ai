"""API の入出力スキーマ（Pydantic v2）。"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


# --- User ---
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: dt.datetime


# --- Message ---
class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    conversation_id: int
    role: str
    content: str
    meta: dict | None = None
    created_at: dt.datetime


# --- Conversation ---
class ConversationCreate(BaseModel):
    user_id: int | None = None
    title: str | None = None


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=300)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    created_at: dt.datetime
    updated_at: dt.datetime


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []


# --- Chat ---
class ChatRequest(BaseModel):
    content: str = Field(min_length=1)
    use_tools: bool = True  # Web検索などのツールを使うか


# --- Memory ---
class MemoryCreate(BaseModel):
    user_id: int | None = None
    content: str = Field(min_length=1)
    category: str = "fact"
    importance: int = Field(default=3, ge=1, le=5)


class MemoryUpdate(BaseModel):
    content: str | None = None
    category: str | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None


class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    content: str
    category: str
    importance: int
    status: str
    source_message_id: int | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Research ---
class ResearchRequest(BaseModel):
    query: str = Field(min_length=1)
    include_images: bool = True


class Source(BaseModel):
    n: int
    title: str
    url: str
    snippet: str | None = None


class ResearchResponse(BaseModel):
    query: str
    summary: str
    sources: list[Source] = []
    images: list[str] = []


# --- Transcription ---
class TranscriptionResponse(BaseModel):
    text: str


# --- Config (公開可能な設定をフロントに渡す) ---
class ConfigOut(BaseModel):
    app_name: str
    owner_name: str
    chat_model: str
    embedding_provider: str
    search_enabled: bool
    transcription_enabled: bool
    llm_enabled: bool
