"""app/tools/multimodal/document_tool.py — 文档摘要/问答工具

复用 rag.parser.extract_file_text 解析 PDF/Word/TXT/MD（不重写解析），
再用 LLM 对文档做摘要或回答问题；结果登记为 markdown 产物。
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult

_MAX_DOC_CHARS = 12000


class DocumentArgs(BaseModel):
    query: str = Field(default="", description="文档文件名关键词；留空则取最近上传的文档")
    question: str = Field(default="", description="对文档的提问；留空则做整体摘要")


class DocumentTool(BaseTool):
    name = "document_qa"
    description = "解析用户上传的文档（PDF/Word/TXT/MD）并做摘要或问答。用户要求总结文档、问文档内容时使用。"
    args_schema = DocumentArgs
    timeout_s = 60.0

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()

        from app.services.multimodal import is_feature_enabled, resolve_user_file
        from app.services.multimodal.helpers import DOC_EXTS

        if not is_feature_enabled("documentEnabled"):
            return ToolResult(output="", duration_ms=0, error="文档解析功能已被管理员关闭")

        query = str(kwargs.get("query") or "").strip()
        question = str(kwargs.get("question") or "").strip()
        target, path, hint = resolve_user_file(kwargs.get("_user_id"), query, exts=DOC_EXTS)
        if target is None or path is None:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=hint)

        from app.services.rag.rag_service import extract_file_text

        text = (extract_file_text(path) or "").strip()
        if not text or text.startswith("[Unsupported"):
            return ToolResult(
                output="",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=f"无法解析文档「{target.original_name}」的文本内容",
            )
        clipped = text[:_MAX_DOC_CHARS]

        from langchain_core.messages import HumanMessage

        from app.llm.factory import create_chat_model

        if question:
            prompt = f"以下是文档《{target.original_name}》的内容，请据此回答问题。\n\n【文档】\n{clipped}\n\n【问题】\n{question}"
            title = f"文档问答 · {target.original_name}"
        else:
            prompt = f"请对以下文档《{target.original_name}》做结构化摘要（要点 + 关键信息），使用 emoji 分节。\n\n{clipped}"
            title = f"文档摘要 · {target.original_name}"

        try:
            llm = create_chat_model()
            resp = await llm.ainvoke([HumanMessage(content=prompt)])
            answer = resp.content if isinstance(resp.content, str) else str(resp.content)
        except Exception as exc:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=f"文档处理失败：{exc}")

        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(
            output=f"{hint}\n\n{answer}",
            duration_ms=duration_ms,
            artifact={"type": "markdown", "title": title, "content": answer},
        )
