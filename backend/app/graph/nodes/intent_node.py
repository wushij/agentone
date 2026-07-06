"""backend/app/graph/nodes/intent_node.py"""

from __future__ import annotations

import re

from app.graph.state import AgentState, IntentType
from app.tools.calculator import extract_expression

_CALC_HINT = re.compile(
    r"(计算|算一下|帮我算|请计算|calculate|calc|等于多少|是多少)",
    re.IGNORECASE,
)
_MATH_EXPR = re.compile(r"[\d]+\s*[\+\-\*\/×÷]\s*[\d]+")


def detect_intent(user_input: str) -> tuple[IntentType, str, dict]:
    text = user_input.strip()

    if _CALC_HINT.search(text) or _MATH_EXPR.search(text):
        expression = extract_expression(text)
        if expression and re.search(r"\d", expression):
            return "calculator", "calculator", {"expression": expression}

    lowered = text.lower()
    if any(k in lowered for k in ("搜索", "search", "查一下", "查询资料")):
        return "search", "search", {"query": text}
    if any(k in lowered for k in ("数据库", "sql", "查询表")):
        return "database", "database", {"query": text}
    if any(k in lowered for k in ("文件", "读取", "上传", "file")):
        return "file", "file", {"path": text}

    return "chat", "", {}


async def intent_node(state: AgentState) -> dict:
    if (state.get("metadata") or {}).get("enable_tools") is False:
        return {
            "intent": "chat",
            "tool_name": "",
            "tool_input": {},
            "current_node": "intent",
            "metadata": {"detected_intent": "chat", "tools_disabled": True},
        }

    user_input = state.get("user_input") or ""
    intent, tool_name, tool_input = detect_intent(user_input)
    return {
        "intent": intent,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "current_node": "intent",
        "metadata": {"detected_intent": intent},
    }
