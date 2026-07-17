"""backend/app/tools/calculator.py"""

from __future__ import annotations

import ast
import math
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

_ALLOWED_FUNCS: dict[str, Any] = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
}

_ALLOWED_CONSTS = {
    "pi": math.pi,
    "e": math.e,
}

_CN_OPERATOR_REPLACEMENTS = (
    ("乘以", "*"),
    ("乘上", "*"),
    ("除以", "/"),
    ("除上", "/"),
    ("加上", "+"),
    ("减去", "-"),
    ("乘", "*"),
    ("除", "/"),
    ("加", "+"),
    ("减", "-"),
)


def normalize_chinese_operators(text: str) -> str:
    result = text
    for cn, op in _CN_OPERATOR_REPLACEMENTS:
        result = result.replace(cn, op)
    result = re.sub(r"(\d)\s*[xX]\s*(\d)", r"\1*\2", result)
    return result


def looks_like_calculation(text: str) -> bool:
    normalized = normalize_chinese_operators(text.strip())
    if re.search(r"\d+\s*[\+\-\*\/×÷]\s*\d+", normalized):
        return True
    if re.search(r"\b(sqrt|abs|log|sin|cos|tan)\s*\(", normalized, re.I):
        return True
    return bool(re.search(r"\d+\s*%", normalized))


def _normalize_expression(text: str) -> str:
    normalized = normalize_chinese_operators(text)
    normalized = normalized.replace("×", "*").replace("÷", "/").replace("（", "(").replace("）", ")")
    normalized = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", normalized)
    normalized = re.sub(r"[^\d\+\-\*\/\(\)\.\sa-zA-Z_,]", "", normalized)
    return normalized.strip()


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_CONSTS:
            return float(_ALLOWED_CONSTS[node.id])
        raise ValueError(f"不支持的常量或变量: {node.id}")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("仅支持简单函数调用")
        fname = node.func.id.lower()
        if fname not in _ALLOWED_FUNCS:
            raise ValueError(f"不支持的函数: {fname}")
        if node.keywords:
            raise ValueError("不支持关键字参数")
        args = [_safe_eval(arg) for arg in node.args]
        return float(_ALLOWED_FUNCS[fname](*args))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return float(_ALLOWED_OPS[type(node.op)](_safe_eval(node.operand)))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return float(_ALLOWED_OPS[type(node.op)](left, right))
    raise ValueError("表达式包含不支持的运算符")


def evaluate_expression(expression: str) -> tuple[str, str]:
    expr = _normalize_expression(expression)
    if not expr:
        raise ValueError("无法解析数学表达式")
    tree = ast.parse(expr, mode="eval")
    value = _safe_eval(tree)
    if value == int(value):
        result = str(int(value))
    else:
        result = str(round(value, 10)).rstrip("0").rstrip(".")
    return expr, result


def extract_expression(user_input: str) -> str:
    text = normalize_chinese_operators(user_input.strip())
    for prefix in ("计算", "算一下", "帮我算", "请计算", "calculate", "calc", "等于多少"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix) :].strip(" ：:，,？?")
            break
    match = re.search(r"[\d\+\-\*\/\(\)×÷\.\sa-zA-Z_,%]+", text)
    if match:
        return _normalize_expression(match.group(0))
    return _normalize_expression(text)


class CalculatorTool(BaseTool):
    name = "calculator"
    description = (
        "安全数学计算器：四则运算、括号、幂运算、百分比，"
        "以及 sqrt/abs/round/min/max/log/sin/cos/tan 等常用函数"
    )

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        expression = kwargs.get("expression") or kwargs.get("input") or ""
        try:
            expr, result = evaluate_expression(str(expression))
            output = f"计算式：{expr}\n结果：{result}"
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output=output, duration_ms=duration_ms)
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output="", duration_ms=duration_ms, error=str(exc))
