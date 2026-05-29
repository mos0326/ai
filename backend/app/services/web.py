"""URL からの本文抽出（軽量スクレイピング）。"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

_TIMEOUT = httpx.Timeout(20.0)
_UA = "Mozilla/5.0 (compatible; PersonalAI/0.1; +https://example.local)"


async def fetch_readable(url: str, max_chars: int = 6000) -> str:
    """ページを取得し、スクリプト等を除いた本文テキストを返す。"""
    async with httpx.AsyncClient(
        timeout=_TIMEOUT, follow_redirects=True, headers={"User-Agent": _UA}
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    text = soup.get_text(separator="\n")
    # 連続する空行を圧縮
    lines = [ln.strip() for ln in text.splitlines()]
    text = "\n".join(ln for ln in lines if ln)

    body = text[:max_chars]
    return f"{title}\n\n{body}" if title else body
