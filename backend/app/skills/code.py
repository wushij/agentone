"""app/skills/code.py — 代码技能（真实 LLM 实现）"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult


class CodeSkill(BaseSkill):
    name = "code"
    description = "代码生成与分析技能"

    async def execute(self, prompt: str = "", language: str = "python", **kwargs: Any) -> SkillResult:
        task = prompt or str(kwargs.get("input") or "")
        if not task:
            return SkillResult(error="缺少代码需求描述")
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            from app.llm.factory import create_chat_model

            llm = create_chat_model()
            response = await llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            f"你是资深 {language} 工程师。根据需求生成可运行的高质量代码，"
                            "带必要注释；只输出代码与简要说明。"
                        )
                    ),
                    HumanMessage(content=task),
                ]
            )
            output = response.content if isinstance(response.content, str) else str(response.content)
            return SkillResult(output=output, metadata={"language": language})
        except Exception as exc:  # noqa: BLE001
            return SkillResult(error=str(exc), metadata={"language": language})
