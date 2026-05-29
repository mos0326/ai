"""DB操作の小さなヘルパー。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Conversation, User

settings = get_settings()


def get_or_create_default_user(db: Session) -> User:
    """単一ユーザーのパーソナルアプリ想定。最初のユーザーを返し、無ければ作る。"""
    user = db.scalars(select(User).order_by(User.id)).first()
    if user is None:
        user = User(name=settings.owner_name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def resolve_user_id(db: Session, user_id: int | None) -> int:
    if user_id is not None:
        return user_id
    return get_or_create_default_user(db).id


def get_conversation_or_404(db: Session, conversation_id: int) -> Conversation:
    from fastapi import HTTPException

    conv = db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="会話が見つかりません")
    return conv
