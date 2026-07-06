"""backend/app/tools/file_tool.py — 用户文件读取工具"""

from __future__ import annotations

import time
from typing import Any

from app.db.session import SessionLocal
from app.services.file_service import FileService
from app.services.rag_service import extract_file_text
from app.tools.base import BaseTool, ToolResult


class FileTool(BaseTool):
    name = "file"
    description = "读取用户已上传文件的内容摘要"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        user_id = kwargs.get("_user_id")
        query = str(kwargs.get("path") or kwargs.get("query") or kwargs.get("input") or "").strip()
        if not user_id:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="无法识别用户上下文",
            )

        db = SessionLocal()
        try:
            files = FileService(db).list_files(int(user_id))
            if not files:
                return ToolResult(
                    output="当前用户暂无已上传文件，请先在文件中心上传。",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                )

            target = None
            if query:
                lowered = query.lower()
                for row in files:
                    if lowered in row.original_name.lower():
                        target = row
                        break
            if target is None:
                target = files[0]

            path = FileService(db).resolve_path(target)
            text = extract_file_text(path)
            preview = text[:2000] + ("…" if len(text) > 2000 else "")
            output = f"文件：{target.original_name}\n大小：{target.size_bytes} bytes\n\n{preview}"
            return ToolResult(output=output, duration_ms=int((time.perf_counter() - started) * 1000))
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
        finally:
            db.close()
