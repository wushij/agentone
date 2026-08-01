"""app/tools/multimodal/ocr_tool.py — OCR 文本提取工具

默认走视觉模型做 OCR（零重依赖）；若安装了 PaddleOCR 则可作为可选高精度后端。
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult

_OCR_PROMPT = "请对这张图片做 OCR，逐行提取其中所有文字，原样输出（保留表格/票据的结构），不要添加解释。"


class OCRArgs(BaseModel):
    query: str = Field(default="", description="图片文件名关键词；留空则取最近上传的图片")


class OCRTool(BaseTool):
    name = "ocr_extract"
    description = "从图片中提取文字（发票/证件/合同/截图 OCR）。用户要求识别图中文字、提取票据/证件信息时使用。"
    args_schema = OCRArgs
    timeout_s = 60.0

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()

        from app.services.multimodal import IMAGE_EXTS, is_feature_enabled, resolve_user_file, vision_chat

        if not is_feature_enabled("ocrEnabled"):
            return ToolResult(output="", duration_ms=0, error="OCR 功能已被管理员关闭")

        query = str(kwargs.get("query") or "").strip()
        target, path, hint = resolve_user_file(kwargs.get("_user_id"), query, exts=IMAGE_EXTS)
        if target is None or path is None:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=hint)

        try:
            text = await vision_chat(path, _OCR_PROMPT)
        except Exception as exc:
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
        duration_ms = int((time.perf_counter() - started) * 1000)
        # 提取结果登记为 markdown 产物，前端可查看/下载
        return ToolResult(
            output=f"{hint}\n\n{text}",
            duration_ms=duration_ms,
            artifact={"type": "markdown", "title": f"OCR · {target.original_name}", "content": text},
        )
