"""記憶（memories）の閲覧・手動編集。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..models import Memory
from ..services import embeddings

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("", response_model=list[schemas.MemoryOut])
def list_memories(
    user_id: int | None = None,
    include_superseded: bool = False,
    db: Session = Depends(get_db),
):
    uid = crud.resolve_user_id(db, user_id)
    stmt = select(Memory).where(Memory.user_id == uid)
    if not include_superseded:
        stmt = stmt.where(Memory.status == "active")
    stmt = stmt.order_by(Memory.importance.desc(), Memory.updated_at.desc())
    return list(db.scalars(stmt))


@router.post("", response_model=schemas.MemoryOut, status_code=201)
async def create_memory(
    payload: schemas.MemoryCreate, db: Session = Depends(get_db)
):
    uid = crud.resolve_user_id(db, payload.user_id)
    emb = await embeddings.embed_text(payload.content)
    mem = Memory(
        user_id=uid,
        content=payload.content,
        category=payload.category,
        importance=payload.importance,
        embedding=emb,
    )
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem


@router.patch("/{memory_id}", response_model=schemas.MemoryOut)
async def update_memory(
    memory_id: int, payload: schemas.MemoryUpdate, db: Session = Depends(get_db)
):
    mem = db.get(Memory, memory_id)
    if mem is None:
        raise HTTPException(status_code=404, detail="記憶が見つかりません")
    if payload.content is not None:
        mem.content = payload.content
        mem.embedding = await embeddings.embed_text(payload.content)
    if payload.category is not None:
        mem.category = payload.category
    if payload.importance is not None:
        mem.importance = payload.importance
    if payload.status is not None:
        mem.status = payload.status
    db.commit()
    db.refresh(mem)
    return mem


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    mem = db.get(Memory, memory_id)
    if mem is None:
        raise HTTPException(status_code=404, detail="記憶が見つかりません")
    db.delete(mem)
    db.commit()
