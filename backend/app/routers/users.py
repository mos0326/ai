"""ユーザー関連エンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def get_me(db: Session = Depends(get_db)):
    """既定ユーザーを返す（無ければ作成）。単一ユーザー運用の入口。"""
    return crud.get_or_create_default_user(db)


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.id)))


@router.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
