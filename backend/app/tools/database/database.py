"""app/tools/database/database.py — 只读数据库查询工具"""

from __future__ import annotations

import re
import time
from typing import Any

from sqlalchemy import text

from app.db.session import SessionLocal
from app.tools.base import BaseTool, ToolResult
from app.tools.text.tool_text import extract_database_query

_SCHEMA_GUIDE = """系统只读数据库可用表说明：

| 表名 | 说明 | 常用字段 |
|------|------|----------|
| users | 用户账号 | id, username, nickname, role, status, created_at |
| conversations | 会话 | id, user_id, title, is_archived, created_at |
| messages | 消息 | id, conversation_id, role, content, tokens, created_at |
| tool_logs | 工具调用日志 | tool_name, params, result, duration_ms, status, created_at |
| prompts | Prompt 模板 | name, type, version, enabled |
| model_configs | 模型配置 | name, provider, model_name, is_default, status |
| file_assets | 用户文件 | user_id, original_name, mime_type, size_bytes, created_at |
| audit_logs | 审计日志 | module, action, detail, created_at |
| tool_configs | 工具开关 | name, enabled |
| system_settings | 系统配置 | key, value |

仅支持 SELECT 只读查询。也可直接问：「有多少用户」「会话数量」「消息总数」等。"""

_PRESET_QUERIES: list[tuple[str, str]] = [
    (r"(用户|账号).*(数|量|多少|统计)|多少.*(用户|账号)|用户总数", "SELECT COUNT(*) AS total FROM users"),
    (r"(正常|启用).*(用户|账号)", "SELECT COUNT(*) AS total FROM users WHERE status = 1"),
    (r"(会话|对话).*(数|量|多少|统计)|多少.*(会话|对话)", "SELECT COUNT(*) AS total FROM conversations"),
    (r"(消息).*(数|量|多少|统计)|多少.*(消息)", "SELECT COUNT(*) AS total FROM messages"),
    (r"(工具|调用).*(数|量|多少|统计)|tool.*log", "SELECT COUNT(*) AS total FROM tool_logs"),
    (r"(审计|操作).*(日志|数|量)|audit", "SELECT COUNT(*) AS total FROM audit_logs"),
    (r"(文件).*(数|量|多少|统计)|多少.*(文件)", "SELECT COUNT(*) AS total FROM file_assets"),
    (r"(prompt|提示词).*(数|量|多少)", "SELECT COUNT(*) AS total FROM prompts"),
    (r"(模型).*(数|量|多少|配置)", "SELECT COUNT(*) AS total FROM model_configs"),
    (
        r"最近.*(工具|调用)|工具.*(最近|日志)",
        "SELECT tool_name, status, duration_ms, created_at FROM tool_logs ORDER BY created_at DESC LIMIT 10",
    ),
    (
        r"最近.*(审计|操作)|审计.*(最近|日志)",
        "SELECT module, action, detail, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10",
    ),
    (
        r"最近.*(用户|注册)",
        "SELECT username, nickname, role, created_at FROM users ORDER BY created_at DESC LIMIT 10",
    ),
]

_TABLE_HINTS = ("有哪些表", "什么表", "表结构", "数据表", "表列表", "数据库结构")


def wants_schema_guide(text: str) -> bool:
    return any(h in text for h in _TABLE_HINTS)


def resolve_database_sql(user_input: str) -> str | None:
    text = extract_database_query(user_input)
    if not text:
        return None
    if text.lower().startswith("select"):
        return text
    for pattern, sql in _PRESET_QUERIES:
        if re.search(pattern, text, re.IGNORECASE):
            return sql
    return None


def _validate_select_sql(sql: str) -> str | None:
    cleaned_sql = re.sub(r"\s+", " ", sql).strip().lower()
    if not cleaned_sql.startswith("select"):
        return "安全限制：该数据库工具仅支持只读 SELECT 查询。"
    forbidden = [
        "insert", "update", "delete", "drop", "alter",
        "truncate", "replace", "grant", "revoke", "create",
    ]
    for word in forbidden:
        if re.search(r"\b" + re.escape(word) + r"\b", cleaned_sql):
            return f"安全限制：SQL 语句中包含禁用关键字 '{word}'"
    return None


def _format_rows(keys: list[str], rows: list) -> str:
    if not rows:
        return "查询成功，但没有返回任何数据。"
    lines = [" | ".join(keys)]
    lines.append("-" * min(80, len(lines[0])))
    for row in rows[:50]:
        lines.append(" | ".join(str(val) for val in row))
    suffix = f"\n（共 {len(rows)} 行，仅展示前 {min(len(rows), 50)} 行）" if len(rows) > 50 else ""
    return f"查询成功，返回 {len(rows)} 行数据：\n" + "\n".join(lines) + suffix


class DatabaseTool(BaseTool):
    name = "database"
    description = (
        "系统只读数据库查询：支持自然语言统计（用户数、会话数等）"
        "与手写 SELECT 查询"
    )

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        raw = str(kwargs.get("sql") or kwargs.get("query") or kwargs.get("input") or "").strip()
        if not raw:
            return ToolResult(
                output=_SCHEMA_GUIDE,
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

        if wants_schema_guide(raw):
            return ToolResult(
                output=_SCHEMA_GUIDE,
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

        sql = resolve_database_sql(raw)
        if not sql:
            return ToolResult(
                output=(
                    "未能将问题转换为 SQL。你可以：\n"
                    "1. 直接写 SELECT 语句，例如：SELECT COUNT(*) FROM users\n"
                    "2. 用自然语言问：有多少用户 / 会话数量 / 最近工具调用\n"
                    "3. 问「有哪些表」查看表结构说明\n\n"
                    + _SCHEMA_GUIDE
                ),
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

        validation_error = _validate_select_sql(sql)
        if validation_error:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=validation_error,
            )

        db = SessionLocal()
        try:
            result = db.execute(text(sql))
            if result.returns_rows:
                rows = result.fetchall()
                keys = list(result.keys())
                output = _format_rows(keys, rows)
                output = f"执行 SQL：{sql}\n\n{output}"
            else:
                output = f"执行 SQL：{sql}\n\n查询执行成功，无行数据返回。"

            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output=output, duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output="", duration_ms=duration_ms, error=str(exc))
        finally:
            db.close()