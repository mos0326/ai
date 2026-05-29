"""埋め込みベクトル生成。プロバイダ切替（openai / voyage / local）対応。

キーが無いプロバイダが選ばれた場合は安全に local フォールバックへ降格する。
local はハッシュtrickによる決定論的な簡易埋め込み（意味検索の精度は劣るが、
キー無しでもシステムが動くようにするための開発用フォールバック）。
"""

from __future__ import annotations

import hashlib
import math
import re

import httpx

from ..config import get_settings

settings = get_settings()

_TIMEOUT = httpx.Timeout(30.0)


def _effective_provider() -> str:
    """設定とキーの有無から、実際に使うプロバイダを決定する。"""
    provider = settings.resolved_embedding_provider
    if provider == "openai" and not settings.openai_api_key:
        return "local"
    if provider == "voyage" and not settings.voyage_api_key:
        return "local"
    return provider


async def embed_text(text: str) -> list[float]:
    vecs = await embed_texts([text])
    return vecs[0]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    provider = _effective_provider()
    if provider == "openai":
        return await _openai_embed(texts)
    if provider == "voyage":
        return await _voyage_embed(texts)
    return [_local_embed(t) for t in texts]


# --- OpenAI ---
async def _openai_embed(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.embedding_model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
    data.sort(key=lambda d: d["index"])
    return [d["embedding"] for d in data]


# --- Voyage AI ---
async def _voyage_embed(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
            json={"model": settings.voyage_embedding_model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
    data.sort(key=lambda d: d["index"])
    return [d["embedding"] for d in data]


# --- ローカル決定論的フォールバック ---
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _hash_to_index(token: str, dim: int) -> tuple[int, float]:
    h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
    idx = h % dim
    sign = 1.0 if (h >> 8) & 1 else -1.0
    return idx, sign


def _local_embed(text: str) -> list[float]:
    dim = settings.local_embedding_dim
    vec = [0.0] * dim
    text = text.lower().strip()

    # 単語トークン
    for tok in _WORD_RE.findall(text):
        idx, sign = _hash_to_index("w:" + tok, dim)
        vec[idx] += sign

    # 文字3-gram（日本語など空白区切りでない言語向けの曖昧マッチ用）
    compact = re.sub(r"\s+", "", text)
    for i in range(len(compact) - 2):
        gram = compact[i : i + 3]
        idx, sign = _hash_to_index("g:" + gram, dim)
        vec[idx] += sign * 0.5

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
