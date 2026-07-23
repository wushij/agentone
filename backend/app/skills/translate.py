"""app/skills/translate.py — 翻译技能"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult


class TranslateSkill(BaseSkill):
    name = "translate"
    description = "翻译技能"

    async def execute(self, text: str = "", target_lang: str = "en", **kwargs: Any) -> SkillResult:
        return SkillResult(output=f"翻译: {text}", metadata={"target_lang": target_lang})