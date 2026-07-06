"""backend/app/tools/calculator.py"""

from __future__ import annotations

import ast
import operator
import re
import time
from typing import Any

from app.tools.base import BaseTool, ToolResult

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _normalize_expression(text: str) -> str:
    normalized = text.replace("×", "*").replace("÷", "/").replace("（", "(").replace("）", ")")
    normalized = re.sub(r"[^\d\+\-\*\/\(\)\.\s]", "", normalized)
    return normalized.strip()


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    raise ValueError("表达式包含不支持的运算符")


def evaluate_expression(expression: str) -> str:
    expr = _normalize_expression(expression)
    if not expr:
        raise ValueError("无法解析数学表达式")
    tree = ast.parse(expr, mode="eval")
    value = _safe_eval(tree)
    if value == int(value):
        return str(int(value))
    return str(round(value, 10)).rstrip("0").rstrip(".")


def extract_expression(user_input: str) -> str:
    text = user_input.strip()
    for prefix in ("计算", "算一下", "帮我算", "请计算", "calculate", "calc"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix) :].strip(" ：:，,")
            break
    match = re.search(r"[\d\+\-\*\/\(\)×÷\.\s]+", text)
    if match:
        return _normalize_expression(match.group(0))
    return _normalize_expression(text)


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "安全数学表达式计算器"

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        expression = kwargs.get("expression") or kwargs.get("input") or ""
        try:
            output = evaluate_expression(str(expression))
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output=output, duration_ms=duration_ms)
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output="", duration_ms=duration_ms, error=str(exc))
