"""Anthropic Claude 連携。

- complete(): 非ストリーミング（記憶抽出・リサーチ要約に使用）
- stream_agent(): ストリーミング + ツール使用ループ（チャットに使用）
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from ..config import get_settings

settings = get_settings()


class LLMNotConfigured(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "ANTHROPIC_API_KEY が未設定です。backend/.env に設定してください。"
        )


def is_enabled() -> bool:
    return bool(settings.anthropic_api_key)


def _client():
    if not settings.anthropic_api_key:
        raise LLMNotConfigured()
    from anthropic import AsyncAnthropic

    return AsyncAnthropic(api_key=settings.anthropic_api_key)


def _blocks_to_dicts(content: list[Any]) -> list[dict]:
    """SDK のレスポンス content ブロックを、次ターンに渡せる素の dict に変換。"""
    out: list[dict] = []
    for b in content:
        if b.type == "text":
            out.append({"type": "text", "text": b.text})
        elif b.type == "tool_use":
            out.append(
                {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
            )
    return out


async def complete(
    system: str,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    client = _client()
    resp = await client.messages.create(
        model=model or settings.chat_model,
        system=system,
        messages=messages,
        max_tokens=max_tokens or settings.max_tokens,
    )
    return "".join(b.text for b in resp.content if b.type == "text")


ToolDispatch = Callable[[str, dict], Awaitable[str]]


async def stream_agent(
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    dispatch: ToolDispatch | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    max_iterations: int = 5,
) -> AsyncGenerator[dict, None]:
    """ストリーミングしつつ、ツール使用があれば実行して継続する。

    yield されるイベント dict の type:
      text       : {"delta": str}        本文の差分
      tool_start : {"name": str}         ツール呼び出しブロックの開始
      tool_call  : {"name", "input"}     実際に実行するツールと引数
      tool_done  : {"name"}              ツール実行完了
      final      : {"text", "content"}   最終本文と assistant content ブロック
    """
    client = _client()
    model = model or settings.chat_model
    max_tokens = max_tokens or settings.max_tokens
    convo: list[dict] = list(messages)

    assistant_content: list[dict] = []
    text_acc = ""

    for _ in range(max_iterations):
        text_acc = ""
        kwargs: dict[str, Any] = dict(
            model=model, system=system, messages=convo, max_tokens=max_tokens
        )
        if tools:
            kwargs["tools"] = tools

        async with client.messages.stream(**kwargs) as stream:
            async for ev in stream:
                if ev.type == "content_block_delta" and ev.delta.type == "text_delta":
                    text_acc += ev.delta.text
                    yield {"type": "text", "delta": ev.delta.text}
                elif ev.type == "content_block_start" and getattr(
                    ev.content_block, "type", None
                ) == "tool_use":
                    yield {"type": "tool_start", "name": ev.content_block.name}
            final = await stream.get_final_message()

        assistant_content = _blocks_to_dicts(final.content)
        convo.append({"role": "assistant", "content": assistant_content})

        if final.stop_reason == "tool_use" and dispatch is not None:
            tool_results = []
            for block in final.content:
                if block.type != "tool_use":
                    continue
                yield {"type": "tool_call", "name": block.name, "input": block.input}
                try:
                    result = await dispatch(block.name, block.input)
                except Exception as e:  # ツール失敗はモデルに伝えて続行
                    result = f"ツール実行エラー: {e}"
                yield {"type": "tool_done", "name": block.name}
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
            convo.append({"role": "user", "content": tool_results})
            continue

        yield {"type": "final", "text": text_acc, "content": assistant_content}
        return

    # max_iterations 到達時の保険
    yield {"type": "final", "text": text_acc, "content": assistant_content}
