"""リサーチ機能: Web検索 → 複数ソース取得 → Claudeで統合要約（出典付き）。"""

from __future__ import annotations

import asyncio

from .. import prompts
from ..config import get_settings
from . import llm
from . import search as search_svc
from . import web as web_svc

settings = get_settings()


async def run_research(query: str, include_images: bool = True) -> dict:
    data = await search_svc.web_search(
        query, settings.research_max_results, include_images
    )
    results = data["results"][: settings.research_max_results]
    images = (data.get("images") or [])[:8]

    sources = [
        {
            "n": i,
            "title": r["title"],
            "url": r["url"],
            "snippet": (r.get("content") or "")[:300],
        }
        for i, r in enumerate(results, 1)
    ]

    # 上位ページを並列フェッチして本文を厚くする（失敗は無視して抜粋にフォールバック）
    fetch_n = min(settings.research_fetch_pages, len(results))
    fetched: list = []
    if fetch_n:
        fetched = await asyncio.gather(
            *[web_svc.fetch_readable(results[i]["url"], 3000) for i in range(fetch_n)],
            return_exceptions=True,
        )

    blocks = []
    for i, r in enumerate(results, 1):
        body = r.get("content") or ""
        if i - 1 < fetch_n:
            got = fetched[i - 1]
            if not isinstance(got, Exception) and got:
                body = got
        blocks.append(f"[{i}] {r['title']}\nURL: {r['url']}\n{body[:1800]}")
    sources_block = "\n\n".join(blocks)

    if llm.is_enabled() and sources:
        summary = await llm.complete(
            prompts.RESEARCH_SYSTEM,
            [
                {
                    "role": "user",
                    "content": prompts.build_research_user_prompt(query, sources_block),
                }
            ],
            model=settings.research_model,
            max_tokens=1500,
        )
    elif not sources:
        summary = "検索結果が得られませんでした。クエリを変えて試してください。"
    else:
        summary = (
            "（ANTHROPIC_API_KEY が未設定のためAIによる要約は省略しました。"
            "下の出典を直接参照してください。）"
        )

    return {"query": query, "summary": summary, "sources": sources, "images": images}
