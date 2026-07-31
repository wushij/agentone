"""app/skills/summarize.py — 摘要技能（真实 LLM 实现，失败回退截断）"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult


class SummarizeSkill(BaseSkill):
    name = "summarize"
    description = "文本摘要技能"

    async def execute(self, text: str = "", max_words: int = 200, **kwargs: Any) -> SkillResult:
        source = text or str(kwargs.get("input") or "")
        if not source:
            return SkillResult(error="缺少待摘要文本")
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            from app.llm.factory import create_chat_model

            llm = create_chat_model()
            response = await llm.ainvoke(
                [
                    SystemMessage(content=f"你是文本摘要专家。用不超过 {max_words} 字概括要点，保留关键数字与结论。"),
                    HumanMessage(content=source[:12000]),
                ]
            )
            output = response.content if isinstance(response.content, str) else str(response.content)
            return SkillResult(output=output, metadata={"length": len(source)})
        except Exception:
            # LLM 不可用时回退为截断预览，不阻断调用方
            return SkillResult(output=f"摘要: {source[:200]}...", metadata={"length": len(source), "fallback": True})
