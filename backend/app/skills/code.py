"""app/skills/code.py — 代码技能"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult


class CodeSkill(BaseSkill):
    name = "code"
    description = "代码生成与分析技能"

    async def execute(self, prompt: str = "", language: str = "python", **kwargs: Any) -> SkillResult:
        return SkillResult(output=f"代码生成: {prompt}", metadata={"language": language})