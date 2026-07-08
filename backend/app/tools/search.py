"""backend/app/tools/search.py"""

from __future__ import annotations

import time
import urllib.request
import urllib.parse
import re
import html
from typing import Any

from app.tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    name = "search"
    description = "网络搜索引擎，用于根据关键词检索互联网最新公开信息与新闻。"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        query = str(kwargs.get("query") or kwargs.get("input") or "").strip()
        if not query:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="缺少搜索关键词",
            )
        
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
                
                blocks = re.split(r'<div class="[^"]*web-result[^"]*"', html_content)[1:]
                results = []
                for block in blocks[:5]:
                    # Extract title
                    title_match = re.search(r'<a class="result__url"[^>]*>(.*?)</a>', block, re.DOTALL)
                    title = title_match.group(1).strip() if title_match else ""
                    title = re.sub(r'<[^>]+>', '', title)
                    title = html.unescape(title).strip()
                    
                    # Extract snippet
                    snippet_match = re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL)
                    snippet = snippet_match.group(1).strip() if snippet_match else ""
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                    snippet = html.unescape(snippet).strip()
                    
                    # Extract link
                    link_match = re.search(r'<a class="result__url" href="([^"]+)"', block)
                    link = link_match.group(1) if link_match else ""
                    if "uddg=" in link:
                        link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])
                    
                    if title or snippet:
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "link": link
                        })
                
                if not results:
                    output = f"没有找到关于 '{query}' 的搜索结果。"
                else:
                    output_lines = [f"关于 '{query}' 的网络搜索结果：\n"]
                    for i, res in enumerate(results):
                        output_lines.append(f"[{i+1}] {res['title']}")
                        output_lines.append(f"    链接: {res['link']}")
                        output_lines.append(f"    摘要: {res['snippet']}\n")
                    output = "\n".join(output_lines)
                
                duration_ms = int((time.perf_counter() - started) * 1000)
                return ToolResult(output=output, duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output="", duration_ms=duration_ms, error=str(exc))
