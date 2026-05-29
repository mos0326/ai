"""pytest 共通設定。

- backend/ を import パスに追加（`import app` を可能にする）
- テスト用に一時 SQLite DB を使い、外部APIキーは未設定にする
  （local 埋め込みフォールバックで動作確認できる）
これらは app を import する前に実行される必要があるため conftest に置く。
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

# TEST_DATABASE_URL が指定されていればそれを使う（Postgres+pgvector の実テスト用）。
# 未指定なら一時 SQLite。
_db_url = os.environ.get("TEST_DATABASE_URL")
if not _db_url:
    _test_db = os.path.join(tempfile.gettempdir(), "personal_ai_test.db")
    if os.path.exists(_test_db):
        os.remove(_test_db)
    _db_url = f"sqlite:///{_test_db}"

os.environ["DATABASE_URL"] = _db_url
os.environ.setdefault("EMBEDDING_PROVIDER", "local")
os.environ.setdefault("SEARCH_PROVIDER", "tavily")
for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY", "BRAVE_API_KEY"):
    os.environ.pop(key, None)

# TestClient を with 文なしで使う場合 lifespan が走らないため、明示的にDB初期化する。
from app.database import init_db  # noqa: E402

init_db()
