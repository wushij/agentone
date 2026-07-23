"""app/tools/network/search.py — 网络搜索工具"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any

from app.tools.base import BaseTool, ToolResult
from app.tools.text.tool_text import extract_search_query

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _fetch_json(url: str, timeout: int = 8) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None


def _search_ddg_api(query: str) -> list[dict[str, str]]:
    url = (
        "https://api.duckduckgo.com/?"
        + urllib.parse.urlencode(
            {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
        )
    )
    data = _fetch_json(url)
    if not data:
        return []

    results: list[dict[str, str]] = []
    abstract = (data.get("AbstractText") or "").strip()
    if abstract:
        results.append(
            {
                "title": (data.get("Heading") or "即时摘要").strip(),
                "snippet": abstract,
                "link": (data.get("AbstractURL") or "").strip(),
            }
        )

    def collect_topics(topics: list) -> None:
        for item in topics:
            if not isinstance(item, dict):
                continue
            if "Topics" in item:
                collect_topics(item.get("Topics") or [])
                continue
            text = (item.get("Text") or "").strip()
            if not text:
                continue
            link = (item.get("FirstURL") or "").strip()
            title = text.split(" - ", 1)[0] if " - " in text else text[:80]
            snippet = text if len(text) <= 240 else text[:240] + "…"
            results.append({"title": title, "snippet": snippet, "link": link})

    collect_topics(data.get("RelatedTopics") or [])
    return results[:8]


def _search_ddg_html(query: str) -> list[dict[str, str]]:
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            html_content = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    results: list[dict[str, str]] = []
    blocks = re.split(r'<div class="[^"]*result[^"]*"', html_content)[1:]
    for block in blocks[:8]:
        title_match = re.search(
            r'class="result__a"[^>]*>(.*?)</a>|class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>',
            block,
            re.DOTALL,
        )
        title_raw = ""
        if title_match:
            title_raw = title_match.group(1) or title_match.group(2) or ""
        title = re.sub(r"<[^>]+>", "", title_raw)
        title = html.unescape(title).strip()

        snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</', block, re.DOTALL)
        snippet = ""
        if snippet_match:
            snippet = re.sub(r"<[^>]+>", "", snippet_match.group(1))
            snippet = html.unescape(snippet).strip()

        link_match = re.search(r'class="result__a"\s+href="([^"]+)"', block)
        link = ""
        if link_match:
            link = link_match.group(1)
            if "uddg=" in link:
                link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

        if title or snippet:
            results.append({"title": title or "无标题", "snippet": snippet, "link": link})
    return results


def _format_results(query: str, results: list[dict[str, str]]) -> str:
    if not results:
        return f"未找到关于「{query}」的公开网络信息，请尝试换个关键词。"
    lines = [f"关于「{query}」的网络检索结果（共 {len(results)} 条）：\n"]
    for i, res in enumerate(results, 1):
        lines.append(f"[{i}] {res['title']}")
        if res["link"]:
            lines.append(f"    链接: {res['link']}")
        if res["snippet"]:
            lines.append(f"    摘要: {res['snippet']}")
        lines.append("")
    return "\n".join(lines).strip()


class SearchTool(BaseTool):
    name = "search"
    description = "网络搜索：检索互联网公开信息、新闻与百科摘要（DuckDuckGo）"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        raw = str(kwargs.get("query") or kwargs.get("input") or "").strip()
        query = extract_search_query(raw)
        if not query:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="缺少搜索关键词",
            )

        results = _search_ddg_api(query)
        if len(results) < 2:
            html_results = _search_ddg_html(query)
            seen = {r.get("link") or r.get("title") for r in results}
            for item in html_results:
                key = item.get("link") or item.get("title")
                if key not in seen:
                    results.append(item)
                    seen.add(key)

        output = _format_results(query, results[:8])
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(output=output, duration_ms=duration_ms)