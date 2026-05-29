"""APIの基本動作テスト（APIキー無し・local埋め込みで完結）。"""

from fastapi.testclient import TestClient

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
