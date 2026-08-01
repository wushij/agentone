"""app/tools/multimodal/image_tool.py — 图像理解工具（看图问答）"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class ImageArgs(BaseModel):
    query: str = Field(default="", description="图片文件名关键词；留空则取最近上传的图片")
    question: str = Field(default="请详细描述这张图片的内容", description="对图片的提问")


class ImageTool(BaseTool):
    name = "image_analyze"
    description = "分析用户上传的图片并回答问题（图像理解/看图问答/图片描述）。用户提到看图、图片内容、这张图时使用。"
    args_schema = ImageArgs
    timeout_s = 60.0

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()

        from app.services.multimodal import IMAGE_EXTS, is_feature_enabled, resolve_user_file, vision_chat

        if not is_feature_enabled("imageEnabled"):
            return ToolResult(output="", duration_ms=0, error="图像理解功能已被管理员关闭")

        query = str(kwargs.get("query") or "").strip()
        question = str(kwargs.get("question") or "请详细描述这张图片的内容").strip()
        user_id = kwargs.get("_user_id")

        file_query = query or question
        target, path, hint = resolve_user_file(user_id, file_query, exts=IMAGE_EXTS)
        if target is None or path is None:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=hint)

        import re
        clean_question = re.sub(r"!\[.*?\]\(.*?\)", "", question).strip()
        if not clean_question:
            clean_question = "请详细描述这张图片的内容"

        try:
            answer = await vision_chat(path, clean_question)
        except Exception as exc:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(output=f"{hint}\n\n{answer}", duration_ms=duration_ms)
