"""backend/app/tools/database_tool.py — 数据库查询占位工具"""

from __future__ import annotations

import time
from typing import Any

from app.tools.base import BaseTool, ToolResult


class DatabaseTool(BaseTool):
    name = "database"
    description = "数据库查询（占位实现，返回模拟结果）"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        query = str(kwargs.get("query") or kwargs.get("input") or "").strip()
        if not query:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="缺少查询语句或描述",
            )
        output = (
            f"【数据库占位】收到查询：{query}\n"
            "当前为 V1.1 占位实现，尚未接入真实数据库连接。"
            "如需数据分析，请描述具体需求，Agent 将基于模型能力协助。"
        )
        return ToolResult(output=output, duration_ms=int((time.perf_counter() - started) * 1000))
