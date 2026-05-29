"""Web検索プロバイダ（Tavily / Brave）。"""

from __future__ import annotations

import httpx

from ..config import get_settings

settings = get_settings()

_TIMEOUT = httpx.Timeout(20.0)


class SearchNotConfigured(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "検索プロバイダのAPIキーが未設定です。"
            "TAVILY_API_KEY または BRAVE_API_KEY を backend/.env に設定してください。"
        )


def is_enabled() -> bool:
    if settings.search_provider == "tavily":
        return bool(settings.tavily_api_key)
    if settings.search_provider == "brave":
        return bool(settings.brave_api_key)
    return False


async def web_search(
    query: str,
    max_results: int | None = None,
    include_images: bool = False,
) -> dict:
    """戻り値: {"results": [{"title","url","content"}], "images": [url, ...]}"""
    max_results = max_results or settings.research_max_results
    provider = settings.search_provider
    if provider == "tavily" and settings.tavily_api_key:
        return await _tavily(query, max_results, include_images)
    if provider == "brave" and settings.brave_api_key:
        return await _brave(query, max_results)
    raise SearchNotConfigured()


async def _tavily(query: str, max_results: int, include_images: bool) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_images": include_images,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    results = [
        {
            "title": r.get("title") or r.get("url", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in data.get("results", [])
    ]
    return {"results": results, "images": data.get("images", []) or []}


async def _brave(query: str, max_results: int) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "X-Subscription-Token": settings.brave_api_key or "",
                "Accept": "application/json",
            },
            params={"q": query, "count": max_results},
        )
        resp.raise_for_status()
        data = resp.json()
    web = (data.get("web") or {}).get("results", [])
    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("description", ""),
        }
        for r in web[:max_results]
    ]
    return {"results": results, "images": []}
