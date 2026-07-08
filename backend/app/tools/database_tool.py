"""backend/app/tools/database_tool.py"""

from __future__ import annotations

import time
import re
from typing import Any

from sqlalchemy import text
from app.db.session import SessionLocal
from app.tools.base import BaseTool, ToolResult


class DatabaseTool(BaseTool):
    name = "database"
    description = "系统只读数据库查询工具，可执行 SELECT 查询系统状态数据（如用户数、日志量等统计）"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        sql = str(kwargs.get("sql") or kwargs.get("query") or kwargs.get("input") or "").strip()
        if not sql:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="缺少 SQL 查询语句",
            )
        
        # 1. 简易安全检查：只允许 SELECT
        cleaned_sql = re.sub(r"\s+", " ", sql).strip().lower()
        if not cleaned_sql.startswith("select"):
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="安全限制：该数据库工具仅支持只读 SELECT 查询，严禁执行写入、修改或结构变更操作。",
            )
        
        # 2. 检查禁用关键字（防 SQL 注入写/高危行为）
        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "replace", "grant", "revoke"]
        for word in forbidden:
            if re.search(r"\b" + re.escape(word) + r"\b", cleaned_sql):
                return ToolResult(
                    output="",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                    error=f"安全限制：SQL 语句中包含禁用关键字 '{word}'",
                )

        db = SessionLocal()
        try:
            result = db.execute(text(sql))
            if result.returns_rows:
                rows = result.fetchall()
                keys = list(result.keys())
                if not rows:
                    output = "查询成功，但没有返回任何数据。"
                else:
                    lines = [" | ".join(keys)]
                    lines.append("-" * len(lines[0]))
                    for row in rows[:50]:  # 限制最大返回 50 行
                        lines.append(" | ".join(str(val) for val in row))
                    output = f"查询成功，返回 {len(rows)} 行数据：\n" + "\n".join(lines)
            else:
                output = "查询执行成功，无行数据返回。"
            
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output=output, duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output="", duration_ms=duration_ms, error=str(exc))
        finally:
            db.close()
