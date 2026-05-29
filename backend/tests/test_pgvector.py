"""PostgreSQL + pgvector の近傍検索パスのテスト。

通常の SQLite テストでは自動スキップされる。実行するには pgvector 入りの
Postgres を用意し、環境変数で DB を指定して pytest を起動する:

  docker compose up -d
  TEST_DATABASE_URL=postgresql+psycopg://personal_ai:personal_ai@localhost:5432/personal_ai \
  EMBEDDING_PROVIDER=local EMBEDDING_DIM=384 MEMORY_MIN_SIMILARITY=0.0 \
  pytest tests/test_pgvector.py -q
"""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.services import memory

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL", "").startswith("postgresql"),
    reason="Postgres+pgvector が必要（TEST_DATABASE_URL で指定）",
)

client = TestClient(app)


def test_pgvector_retrieval_orders_by_similarity():
    uid = client.get("/api/me").json()["id"]

    client.post(
        "/api/memories",
        json={"content": "私はブラックコーヒーが好き", "category": "preference"},
    )
    client.post(
        "/api/memories",
        json={"content": "週末は近所の山に登るのが習慣", "category": "preference"},
    )

    db = SessionLocal()
    try:
        results = asyncio.run(memory.retrieve(db, uid, "コーヒーは好き？", k=5))
    finally:
        db.close()

    assert results, "pgvector 検索が結果を返すこと"
    # コーヒーに関する記憶が最上位に来る（コサイン距離順）
    assert "コーヒー" in results[0].content
