"""app/skills/summarize.py — 摘要技能"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult


class SummarizeSkill(BaseSkill):
    name = "summarize"
    description = "文本摘要技能"

    async def execute(self, text: str = "", **kwargs: Any) -> SkillResult:
        return SkillResult(output=f"摘要: {text[:200]}...", metadata={"length": len(text)})