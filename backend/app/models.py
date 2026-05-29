"""ORM モデル定義（users / conversations / messages / memories）。

embedding は SQLite では JSON(TEXT) として保存し、類似検索は Python 側で
コサイン類似度を計算する（個人利用の規模なら十分高速）。Postgres + pgvector
へ移行する場合はこの embedding カラムと vectorstore の検索処理を差し替える。
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import get_settings
from .database import Base

_settings = get_settings()

# 埋め込みカラムの型は DB によって切り替える:
#  - PostgreSQL: pgvector の Vector 型（SQL での近傍検索が使える）
#  - それ以外(SQLite): JSON に list[float] を保存し Python 側でコサイン計算
if _settings.is_postgres:
    from pgvector.sqlalchemy import Vector

    _EmbeddingType: object = Vector(_settings.embedding_dim)
else:
    _EmbeddingType = JSON


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memories: Mapped[list["Memory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300), default="新しい会話")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    # 出典・ツール実行ログ・画像URL等を格納（任意）
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    # preference | relationship | project | goal | fact | other
    category: Mapped[str] = mapped_column(String(40), default="fact", index=True)
    source_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    embedding: Mapped[list[float] | None] = mapped_column(_EmbeddingType, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    # active | superseded（矛盾解消で古い記憶を superseded にする）
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="memories")
