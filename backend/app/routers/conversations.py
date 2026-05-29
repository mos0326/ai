"""会話のCRUD。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..models import Conversation

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[schemas.ConversationOut])
def list_conversations(
    user_id: int | None = None, db: Session = Depends(get_db)
):
    uid = crud.resolve_user_id(db, user_id)
    return list(
        db.scalars(
            select(Conversation)
            .where(Conversation.user_id == uid)
            .order_by(Conversation.updated_at.desc())
        )
    )


@router.post("", response_model=schemas.ConversationOut, status_code=201)
def create_conversation(
    payload: schemas.ConversationCreate, db: Session = Depends(get_db)
):
    uid = crud.resolve_user_id(db, payload.user_id)
    conv = Conversation(user_id=uid, title=payload.title or "新しい会話")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=schemas.ConversationDetailOut)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    return crud.get_conversation_or_404(db, conversation_id)


@router.patch("/{conversation_id}", response_model=schemas.ConversationOut)
def update_conversation(
    conversation_id: int,
    payload: schemas.ConversationUpdate,
    db: Session = Depends(get_db),
):
    conv = crud.get_conversation_or_404(db, conversation_id)
    conv.title = payload.title
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conv = crud.get_conversation_or_404(db, conversation_id)
    db.delete(conv)
    db.commit()
