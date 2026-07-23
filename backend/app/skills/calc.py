"""app/skills/calc.py — 计算技能（安全计算器）"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult
from app.tools.compute.calculator import evaluate_expression


class CalcSkill(BaseSkill):
    name = "calc"
    description = "数学计算技能"

    async def execute(self, expression: str = "", **kwargs: Any) -> SkillResult:
        expr = expression or str(kwargs.get("input") or "")
        try:
            normalized, result = evaluate_expression(expr)
            return SkillResult(
                output=f"计算式：{normalized}\n结果：{result}",
                metadata={"expression": normalized, "result": result},
            )
        except Exception as exc:  # noqa: BLE001
            return SkillResult(error=str(exc), metadata={"expression": expr})