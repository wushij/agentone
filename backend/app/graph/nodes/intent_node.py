"""backend/app/graph/nodes/intent_node.py"""

from __future__ import annotations

import re

from app.graph.state import AgentState, IntentType
from app.tools.calculator import extract_expression, looks_like_calculation

_CALC_HINT = re.compile(
    r"(计算|算一下|帮我算|请计算|calculate|calc|等于多少|是多少|多少)",
    re.IGNORECASE,
)

_DEV_VERBS = (
    "怎么开发",
    "如何开发",
    "怎样开发",
    "帮我开发",
    "帮我做",
    "帮我设计",
    "帮我搭建",
    "从零开发",
    "从0开发",
    "开发一个",
    "做一个",
    "设计一个",
    "搭建一个",
    "实现一个",
    "写一个",
)

_SYSTEM_TARGETS = (
    "管理系统",
    "管理平台",
    "平台",
    "小程序",
    "erp",
    "saas",
    "商城",
    "外卖",
    "刷题",
    "图书管理",
    "学生管理",
    "教务",
    "仓储",
    "mes",
)


def _looks_like_prompt_engineering(text: str) -> bool:
    lowered = text.lower()
    has_dev = any(v in text for v in _DEV_VERBS)
    has_target = any(t in lowered for t in _SYSTEM_TARGETS) or "系统" in text
    has_scheme = any(k in text for k in ("开发方案", "技术方案", "实现方案", "架构设计", "技术栈"))
    has_prompt = any(k in lowered for k in ("提示词", "prompt"))

    if has_dev and has_target:
        return True
    if has_target and has_scheme:
        return True
    if has_prompt and (has_dev or has_target):
        return True
    if "管理系统" in text and has_scheme:
        return True
    return False


def detect_intent(user_input: str) -> tuple[IntentType, str, dict]:
    text = user_input.strip()

    if _looks_like_prompt_engineering(text):
        return "prompt_engineer", "", {}

    if _CALC_HINT.search(text) or looks_like_calculation(text):
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
