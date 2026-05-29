"""記憶システム: 会話からの事実抽出・保存・矛盾解消・関連検索。"""

from __future__ import annotations

import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import prompts
from ..config import get_settings
from ..models import Memory, utcnow
from ..vectorstore import cosine_topk
from . import embeddings, llm

settings = get_settings()

VALID_CATEGORIES = {"preference", "relationship", "project", "goal", "fact", "other"}

# 重複・矛盾とみなす類似度のしきい値
_DUPLICATE_THRESHOLD = 0.93
_CONFLICT_THRESHOLD = 0.82


def _parse_json_array(raw: str) -> list[dict]:
    """LLM 出力から JSON 配列を頑健に取り出す。"""
    if not raw:
        return []
    s = raw.strip()
    s = re.sub(r"^```(?:json)?", "", s).strip()
    s = re.sub(r"```$", "", s).strip()
    start, end = s.find("["), s.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    try:
        arr = json.loads(s[start : end + 1])
    except Exception:
        return []
    return [x for x in arr if isinstance(x, dict) and x.get("content")]


def _active_memories(db: Session, user_id: int) -> list[Memory]:
    return list(
        db.scalars(
            select(Memory).where(
                Memory.user_id == user_id, Memory.status == "active"
            )
        )
    )


async def retrieve(
    db: Session, user_id: int, query: str, k: int | None = None
) -> list[Memory]:
    """query に関連する記憶を上位 k 件返す（プロンプト注入用）。"""
    mems = _active_memories(db, user_id)
    if not mems:
        return []
    q = await embeddings.embed_text(query)
    top = cosine_topk(
        q,
        [(m, m.embedding) for m in mems],
        k or settings.memory_top_k,
        settings.memory_min_similarity,
    )
    return [m for m, _ in top]


def format_block(mems: list[Memory]) -> str:
    """記憶をシステムプロンプトに差し込む文字列に整形。"""
    if not mems:
        return ""
    order = ["goal", "project", "relationship", "preference", "fact", "other"]
    mems_sorted = sorted(
        mems,
        key=lambda m: (
            order.index(m.category) if m.category in order else 99,
            -m.importance,
        ),
    )
    return "\n".join(f"- {m.content}" for m in mems_sorted)


async def extract_and_store(
    db: Session,
    user_id: int,
    owner_name: str,
    user_text: str,
    assistant_text: str,
    source_message_id: int | None = None,
) -> list[Memory]:
    """直近の会話から事実を抽出し、重複・矛盾を解消しつつ保存する。"""
    if not settings.memory_extraction_enabled or not llm.is_enabled():
        return []

    raw = await llm.complete(
        prompts.EXTRACTION_SYSTEM,
        [
            {
                "role": "user",
                "content": prompts.build_extraction_user_prompt(
                    owner_name, user_text, assistant_text
                ),
            }
        ],
        model=settings.extraction_model,
        max_tokens=1024,
    )
    facts = _parse_json_array(raw)
    if not facts:
        return []

    existing = _active_memories(db, user_id)
    contents = [f["content"].strip() for f in facts]
    embs = await embeddings.embed_texts(contents)

    stored: list[Memory] = []
    pool: list[tuple[Memory, list[float] | None]] = [
        (m, m.embedding) for m in existing
    ]

    for fact, emb in zip(facts, embs):
        content = fact["content"].strip()
        category = fact.get("category", "fact")
        if category not in VALID_CATEGORIES:
            category = "fact"
        try:
            importance = int(fact.get("importance", 3))
        except (TypeError, ValueError):
            importance = 3
        importance = max(1, min(5, importance))

        top = cosine_topk(emb, pool, k=1, min_similarity=0.0)
        if top:
            match, sim = top[0]
            if sim >= _DUPLICATE_THRESHOLD:
                # ほぼ重複 → 既存を更新し、新規は作らない
                match.content = content
                match.importance = max(match.importance, importance)
                match.updated_at = utcnow()
                continue
            if sim >= _CONFLICT_THRESHOLD and match.category == category:
                # 同種で類似 → 更新/矛盾とみなし旧記憶を superseded に
                match.status = "superseded"

        mem = Memory(
            user_id=user_id,
            content=content,
            category=category,
            importance=importance,
            embedding=emb,
            source_message_id=source_message_id,
        )
        db.add(mem)
        db.flush()
        stored.append(mem)
        pool.append((mem, emb))

    db.commit()
    for m in stored:
        db.refresh(m)
    return stored
