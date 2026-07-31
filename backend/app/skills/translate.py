"""app/skills/translate.py — 翻译技能（真实 LLM 实现）"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult

_LANG_NAMES = {"en": "英文", "zh": "中文", "ja": "日文", "ko": "韩文", "fr": "法文", "de": "德文"}


class TranslateSkill(BaseSkill):
    name = "translate"
    description = "翻译技能"

    async def execute(self, text: str = "", target_lang: str = "en", **kwargs: Any) -> SkillResult:
        source = text or str(kwargs.get("input") or "")
        if not source:
            return SkillResult(error="缺少待翻译文本")
        lang_name = _LANG_NAMES.get(target_lang, target_lang)
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            from app.llm.factory import create_chat_model

            llm = create_chat_model()
            response = await llm.ainvoke(
                [
                    SystemMessage(content=f"你是专业翻译。把用户文本翻译为{lang_name}，只输出译文。"),
                    HumanMessage(content=source[:8000]),
                ]
            )
            output = response.content if isinstance(response.content, str) else str(response.content)
            return SkillResult(output=output, metadata={"target_lang": target_lang})
        except Exception as exc:  # noqa: BLE001
            return SkillResult(error=str(exc), metadata={"target_lang": target_lang})
