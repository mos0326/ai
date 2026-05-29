"""APIの基本動作テスト（APIキー無し・local埋め込みで完結）。"""

from fastapi.testclient import TestClient

import app.services.llm as llm_mod
import app.services.memory as memory_mod
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_config_reports_disabled_without_keys():
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert body["llm_enabled"] is False
    assert body["search_enabled"] is False
    assert body["embedding_provider"] == "local"


def test_me_creates_default_user():
    r = client.get("/api/me")
    assert r.status_code == 200
    assert r.json()["id"] >= 1


def test_conversation_crud():
    created = client.post("/api/conversations", json={}).json()
    cid = created["id"]

    listed = client.get("/api/conversations").json()
    assert any(c["id"] == cid for c in listed)

    detail = client.get(f"/api/conversations/{cid}").json()
    assert detail["id"] == cid
    assert detail["messages"] == []

    renamed = client.patch(f"/api/conversations/{cid}", json={"title": "テスト"}).json()
    assert renamed["title"] == "テスト"


def test_memory_crud_with_local_embedding():
    created = client.post(
        "/api/memories",
        json={"content": "私はブラックコーヒーが好き", "category": "preference"},
    )
    assert created.status_code == 201
    mid = created.json()["id"]

    listed = client.get("/api/memories").json()
    assert any(m["id"] == mid for m in listed)

    client.delete(f"/api/memories/{mid}")


def test_research_requires_search_key():
    r = client.post("/api/research", json={"query": "なにか"})
    assert r.status_code == 400


def test_chat_streams_error_without_llm_key():
    conv = client.post("/api/conversations", json={}).json()
    cid = conv["id"]
    r = client.post(f"/api/conversations/{cid}/chat", json={"content": "こんにちは"})
    assert r.status_code == 200
    text = r.text
    # LLM未設定なので error イベントが流れる
    assert '"type": "error"' in text or '"type":"error"' in text
    assert "ANTHROPIC_API_KEY" in text

    # ユーザーメッセージは保存されている
    detail = client.get(f"/api/conversations/{cid}").json()
    roles = [m["role"] for m in detail["messages"]]
    assert "user" in roles


async def _fake_stream_agent(**kwargs):
    """LLMをモックしたストリーミング（テキスト差分→最終）。"""
    yield {"type": "text", "delta": "こんにちは"}
    yield {"type": "text", "delta": "、元気？"}
    yield {
        "type": "final",
        "text": "こんにちは、元気？",
        "content": [{"type": "text", "text": "こんにちは、元気？"}],
    }


async def _fake_extract(*args, **kwargs):
    return []


def test_chat_stream_happy_path(monkeypatch):
    """LLMをモックし、SSEのdelta/done整形とアシスタントメッセージ保存を検証。"""
    monkeypatch.setattr(llm_mod, "stream_agent", _fake_stream_agent)
    monkeypatch.setattr(memory_mod, "extract_and_store", _fake_extract)

    cid = client.post("/api/conversations", json={}).json()["id"]
    r = client.post(
        f"/api/conversations/{cid}/chat",
        json={"content": "やあ", "use_tools": False},
    )
    assert r.status_code == 200
    body = r.text
    assert '"type": "delta"' in body
    assert "こんにちは" in body
    assert '"type": "done"' in body

    # アシスタントの応答が永続化されている
    detail = client.get(f"/api/conversations/{cid}").json()
    assistant = [m for m in detail["messages"] if m["role"] == "assistant"]
    assert assistant and "こんにちは" in assistant[-1]["content"]
    # 初回メッセージで会話タイトルが内容から設定される
    assert detail["title"] == "やあ"
