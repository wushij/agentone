"""app/skills/rag.py — 知识库检索技能"""

from typing import Any

from app.services.rag.rag_service import RagService, format_kb_retrieve_answer
from app.skills.base import BaseSkill, SkillResult


class RagSkill(BaseSkill):
    name = "rag"
    description = "知识库检索技能"

    async def execute(self, query: str = "", kb_ids: list[str] | None = None, **kwargs: Any) -> SkillResult:
        q = query or str(kwargs.get("input") or "")
        ids = list(kb_ids or kwargs.get("kb_ids") or [])
        if not ids:
            return SkillResult(error="未指定知识库 kb_ids")
        try:
            chunks = await RagService.fetch_kb_chunks_multi(ids, q)
            if not chunks:
                return SkillResult(output="未检索到相关内容", metadata={"count": 0})
            return SkillResult(
                output=format_kb_retrieve_answer(q, chunks),
                metadata={"count": len(chunks)},
            )
        except Exception as exc:  # noqa: BLE001
            return SkillResult(error=str(exc))
