"""app/tools/network/http_request.py — 受策略约束的 HTTP 调用工具（§4.3）

通用 API 调用，仅允许 GET/POST + 超时 + 响应体截断；可选 host 允许清单
（settings_store.httpAllowlist，为空则放行公网 http/https）。
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult

_MAX_BODY = 6000
_TIMEOUT = 15.0


class HttpArgs(BaseModel):
    url: str = Field(description="请求 URL（http/https）")
    method: str = Field(default="GET", description="GET 或 POST")
    body: str = Field(default="", description="POST 请求体（可为 JSON 字符串）")


def _host_allowed(url: str) -> bool:
    try:
        from app.services.system.settings_store import settings_store

        allow = settings_store.get("httpAllowlist", "") or ""
    except Exception:
        allow = ""
    if not allow:
        return True
    host = (urlparse(url).hostname or "").lower()
    hosts = [h.strip().lower() for h in allow.replace("\n", ",").split(",") if h.strip()]
    return any(host == h or host.endswith("." + h) for h in hosts)


class HttpRequestTool(BaseTool):
    name = "http_request"
    description = "受控的通用 HTTP 调用（GET/POST），用于访问外部 API 或网页 JSON 数据"
    args_schema = HttpArgs
    timeout_s = 20.0

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        url = str(kwargs.get("url") or "").strip()
        method = str(kwargs.get("method") or "GET").upper()
        body = str(kwargs.get("body") or "")

        if not url.startswith(("http://", "https://")):
            return ToolResult(output="", duration_ms=0, error="仅支持 http/https URL")
        if method not in ("GET", "POST"):
            return ToolResult(output="", duration_ms=0, error="仅支持 GET/POST 方法")
        if not _host_allowed(url):
            return ToolResult(output="", duration_ms=0, error="安全限制：目标 host 不在允许清单内")

        try:
            import httpx

            async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
                if method == "POST":
                    headers = {"Content-Type": "application/json"} if body.strip().startswith("{") else {}
                    resp = await client.post(url, content=body or None, headers=headers)
                else:
                    resp = await client.get(url)
            text = resp.text[:_MAX_BODY]
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(
                output=f"HTTP {resp.status_code}\n{text}",
                duration_ms=duration_ms,
            )
        except Exception as exc:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=str(exc))
