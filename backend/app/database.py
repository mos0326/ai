"""SQLAlchemy のエンジン / セッション / Base 定義。

SQLite を既定とするが、DATABASE_URL を差し替えれば Postgres 等にも移行できる。
データ層をここに集約しておくことで、将来 pgvector へ移す際の変更範囲を絞る。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

# SQLite はスレッド跨ぎ利用のため check_same_thread=False が必要
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


class Base(DeclarativeBase):
    """全 ORM モデルの基底クラス。"""


def init_db() -> None:
    """テーブルを作成する（存在しなければ）。"""
    if settings.is_postgres:
        # pgvector 拡張を有効化してから（Vector カラム作成のため）
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

    from . import models  # noqa: F401  モデル登録のため import

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依存性注入用の DB セッション。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
