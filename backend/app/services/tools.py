"""チャット用のツール定義とディスパッチ（Web検索 / URL取得）。

出典は SourceCollector に集約し、チャットルーターが assistant メッセージの
meta に保存する。これによりUIで出典一覧を表示できる。
"""

from __future__ import annotations

from ..config import get_settings
from . import search as search_svc
from . import web as web_svc

settings = get_settings()

WEB_SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "Webを検索して最新情報や事実を調べる。調べ物・時事・不確かな事実の確認に使う。"
        "結果はタイトル・URL・抜粋付きで返り、各結果に [n] の出典番号が付く。"
        "回答ではその番号を [1][2] のように引用すること。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "検索クエリ（具体的に）"}
        },
        "required": ["query"],
    },
}

FETCH_URL_TOOL = {
    "name": "fetch_url",
    "description": (
        "指定したURLのページ本文を取得して読む。"
        "検索で見つけたページの詳細を確認したいときに使う。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "取得するURL"}
        },
        "required": ["url"],
    },
}


def available_tools() -> list[dict]:
    """検索が使える時だけツールを提供する。"""
    if search_svc.is_enabled():
        return [WEB_SEARCH_TOOL, FETCH_URL_TOOL]
    return []


class SourceCollector:
    def __init__(self) -> None:
        self.sources: list[dict] = []
        self._by_url: dict[str, int] = {}

    def add(self, title: str, url: str, snippet: str | None = None) -> int:
        if not url:
            return 0
        if url in self._by_url:
            return self._by_url[url]
        n = len(self.sources) + 1
        self.sources.append(
            {"n": n, "title": title or url, "url": url, "snippet": (snippet or "")[:300]}
        )
        self._by_url[url] = n
        return n


def make_dispatch(collector: SourceCollector):
    async def dispatch(name: str, tool_input: dict) -> str:
        if name == "web_search":
            query = (tool_input or {}).get("query", "")
            data = await search_svc.web_search(query, include_images=False)
            results = data["results"][: settings.research_max_results]
            if not results:
                return "検索結果が見つかりませんでした。"
            lines = []
            for r in results:
                n = collector.add(r["title"], r["url"], r["content"])
                lines.append(
                    f"[{n}] {r['title']}\n{r['url']}\n{(r['content'] or '')[:500]}"
                )
            return "\n\n".join(lines)

        if name == "fetch_url":
            url = (tool_input or {}).get("url", "")
            text = await web_svc.fetch_readable(url)
            n = collector.add(url, url, text[:200])
            return f"[{n}] {url}\n\n{text}"

        return f"未知のツール: {name}"

    return dispatch
