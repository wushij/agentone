"""app/tools/file/file.py — 用户文件读取工具"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from app.db.session import SessionLocal
from app.services.file.file_service import FileService
from app.services.rag.rag_service import extract_file_text
from app.tools.base import BaseTool, ToolResult
from app.tools.text.tool_text import extract_file_query, wants_file_list

PREVIEW_LIMIT = 8000


def _score_filename(query: str, filename: str) -> int:
    q = query.lower().strip()
    f = filename.lower()
    if not q:
        return 0
    if q == f:
        return 200
    if f.endswith(q) or f.startswith(q):
        return 150
    if q in f:
        return 120 + len(q)
    tokens = [t for t in q.replace(".", " ").split() if len(t) >= 2]
    score = sum(30 for t in tokens if t in f)
    return score


def _format_file_list(files) -> str:
    lines = [f"共 {len(files)} 个已上传文件：\n"]
    for i, row in enumerate(files, 1):
        created = ""
        if getattr(row, "created_at", None):
            created = row.created_at.strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"[{i}] {row.original_name}  ({row.size_bytes} bytes, {row.mime_type}, {created})"
        )
    lines.append("\n提示：可以说「读取 xxx.pdf」查看具体文件内容。")
    return "\n".join(lines)


def _pick_target(files, query: str):
    if not query:
        return files[0], "已自动选择最新上传的文件"

    scored = [(row, _score_filename(query, row.original_name)) for row in files]
    scored.sort(key=lambda item: (item[1], item[0].created_at or datetime.min), reverse=True)
    best, best_score = scored[0]
    if best_score <= 0:
        return None, f"未找到与「{query}」匹配的文件"
    if best_score >= 120:
        return best, f"已匹配文件「{best.original_name}」"
    return best, f"按模糊匹配选择「{best.original_name}」（相似度较低，可指定更准确的文件名）"


class FileTool(BaseTool):
    name = "file"
    description = "读取用户已上传文件：支持列出文件清单、按文件名模糊匹配、提取文本预览"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        user_id = kwargs.get("_user_id")
        raw = str(kwargs.get("path") or kwargs.get("query") or kwargs.get("input") or "").strip()
        query = extract_file_query(raw)
        if not user_id:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="无法识别用户上下文",
            )

        db = SessionLocal()
        try:
            files, _ = FileService(db).list_files(int(user_id), page=1, size=500)
            if not files:
                return ToolResult(
                    output="当前用户暂无已上传文件，请先在文件中心上传。",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                )

            if wants_file_list(raw):
                output = _format_file_list(files)
                return ToolResult(output=output, duration_ms=int((time.perf_counter() - started) * 1000))

            target, hint = _pick_target(files, query)
            if target is None:
                output = _format_file_list(files)
                return ToolResult(
                    output=f"{hint}\n\n{output}",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                )

            path = FileService(db).resolve_path(target)
            text = extract_file_text(path)
            preview = text[:PREVIEW_LIMIT] + ("…" if len(text) > PREVIEW_LIMIT else "")
            output = (
                f"{hint}\n"
                f"文件：{target.original_name}\n"
                f"类型：{target.mime_type}\n"
                f"大小：{target.size_bytes} bytes\n"
                f"预览字数：{min(len(text), PREVIEW_LIMIT)} / {len(text)}\n\n"
                f"{preview}"
            )
            return ToolResult(output=output, duration_ms=int((time.perf_counter() - started) * 1000))
        except Exception as exc:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
        finally:
            db.close()