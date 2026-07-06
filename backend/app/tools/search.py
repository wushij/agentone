"""backend/app/tools/search.py — 搜索工具占位实现"""

from __future__ import annotations

import time
from typing import Any

from app.tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    name = "search"
    description = "网络搜索（占位实现，返回检索摘要提示）"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        query = str(kwargs.get("query") or kwargs.get("input") or "").strip()
        if not query:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="缺少搜索关键词",
            )
        output = (
            f"【搜索占位】关键词：{query}\n"
            "当前为 V1.1 占位实现，尚未接入真实搜索引擎。"
            "如需准确信息，请直接描述问题，Agent 将基于模型知识回答。"
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(output=output, duration_ms=duration_ms)
