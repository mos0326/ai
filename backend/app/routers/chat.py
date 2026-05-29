"""ストリーミングチャット（SSE）。

フロー:
  1. ユーザーメッセージを保存
  2. 関連する記憶を検索してシステムプロンプトに注入
  3. Claude をストリーミング（必要ならWeb検索ツールを使用）
  4. アシスタントメッセージ（出典付き）を保存
  5. 会話から事実を抽出して記憶に保存
各ステップの進捗を SSE イベントとしてフロントへ流す。
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import crud, prompts, schemas
from ..config import get_settings
from ..database import get_db
from ..models import Conversation, Message, utcnow
from ..services import llm, memory
from ..services import tools as tools_mod
from ..services.search import SearchNotConfigured

settings = get_settings()
router = APIRouter(prefix="/api/conversations", tags=["chat"])

MAX_HISTORY = 20  # 直近何メッセージを文脈に含めるか


def _sse(event_type: str, **data) -> str:
    payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def _history(db: Session, conversation_id: int) -> list[dict]:
    msgs = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id)
        )
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in msgs
        if m.role in ("user", "assistant") and m.content
    ]
    return history[-MAX_HISTORY:]


@router.post("/{conversation_id}/chat")
async def chat(
    conversation_id: int,
    payload: schemas.ChatRequest,
    db: Session = Depends(get_db),
):
    conv = crud.get_conversation_or_404(db, conversation_id)
    user_id = conv.user_id
    owner_name = conv.user.name if conv.user else settings.owner_name

    # 1. ユーザーメッセージを保存
    user_msg = Message(
        conversation_id=conv.id, role="user", content=payload.content
    )
    db.add(user_msg)
    # 初回メッセージなら会話タイトルを内容から設定
    if conv.title in (None, "", "新しい会話"):
        conv.title = payload.content.strip().replace("\n", " ")[:40] or "新しい会話"
    conv.updated_at = utcnow()
    db.commit()
    db.refresh(user_msg)

    # 2. 関連記憶を検索してプロンプト構築
    try:
        mems = await memory.retrieve(db, user_id, payload.content)
    except Exception:
        mems = []
    memory_block = memory.format_block(mems)

    tools = tools_mod.available_tools() if payload.use_tools else []
    system = prompts.build_system_prompt(
        owner_name, memory_block, tools_enabled=bool(tools)
    )
    history = _history(db, conv.id)

    collector = tools_mod.SourceCollector()
    dispatch = tools_mod.make_dispatch(collector)

    async def event_stream() -> AsyncGenerator[str, None]:
        parts: list[str] = []
        final_text = ""
        try:
            yield _sse("start", conversation_id=conv.id, user_message_id=user_msg.id)

            async for ev in llm.stream_agent(
                system=system,
                messages=history,
                tools=tools or None,
                dispatch=dispatch,
                model=settings.chat_model,
            ):
                etype = ev["type"]
                if etype == "text":
                    parts.append(ev["delta"])
                    yield _sse("delta", text=ev["delta"])
                elif etype == "tool_start":
                    yield _sse("tool", phase="start", name=ev["name"])
                elif etype == "tool_call":
                    yield _sse("tool", phase="call", name=ev["name"], input=ev.get("input"))
                elif etype == "tool_done":
                    yield _sse("tool", phase="done", name=ev["name"])
                elif etype == "final":
                    final_text = ev.get("text") or "".join(parts)

            final_text = final_text or "".join(parts)

            # 4. アシスタントメッセージを保存（出典付き）
            meta: dict = {"model": settings.chat_model}
            if collector.sources:
                meta["sources"] = collector.sources
            assistant_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=final_text,
                meta=meta,
            )
            db.add(assistant_msg)
            conv.updated_at = utcnow()
            db.commit()
            db.refresh(assistant_msg)

            if collector.sources:
                yield _sse("sources", sources=collector.sources)
            yield _sse("done", assistant_message_id=assistant_msg.id)

            # 5. 記憶抽出（失敗しても会話は壊さない）
            try:
                added = await memory.extract_and_store(
                    db,
                    user_id,
                    owner_name,
                    payload.content,
                    final_text,
                    source_message_id=assistant_msg.id,
                )
                if added:
                    yield _sse(
                        "memory",
                        added=[
                            {"id": m.id, "content": m.content, "category": m.category}
                            for m in added
                        ],
                    )
            except Exception:
                pass

        except llm.LLMNotConfigured as e:
            yield _sse("error", message=str(e))
        except SearchNotConfigured as e:
            yield _sse("error", message=str(e))
        except Exception as e:  # 想定外も必ずクライアントに伝える
            yield _sse("error", message=f"エラーが発生しました: {e}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
