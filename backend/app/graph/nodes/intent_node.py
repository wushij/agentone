"""backend/app/graph/nodes/intent_node.py"""

from __future__ import annotations

import re

from app.graph.state import AgentState, IntentType
from app.tools.calculator import extract_expression, looks_like_calculation
from app.tools.tool_text import extract_database_query, extract_file_query, extract_search_query, wants_file_list

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
    "帮我写",
    "从零开发",
    "从0开发",
    "开发一个",
    "做一个",
    "设计一个",
    "搭建一个",
    "实现一个",
    "写一个",
    "生成一个",
)

_DESIGN_DOC_HINTS = (
    "设计文档",
    "设计方案",
    "需求文档",
    "技术文档",
    "开发文档",
    "架构设计",
    "技术方案",
    "实现方案",
    "开发方案",
    "技术栈",
)

# 如「学生管理系统」「图书管理平台」
_PROJECT_NAME_RE = re.compile(
    r"[\u4e00-\u9fa5a-zA-Z0-9]{2,24}(管理系统|管理平台|信息平台|业务平台|小程序|系统平台)"
)

# 如「如何做一个学生管理系统」
_DEV_QUESTION_RE = re.compile(
    r"(怎么|如何|怎样|想要|想做|需要做).{0,12}(系统|平台|小程序|管理系统)"
)

_AGENTONE_CTX = ("agentone", "本系统", "本平台", "这个系统", "本助手", "知识库")

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
    if any(k in lowered for k in _AGENTONE_CTX):
        return False

    has_dev = any(v in text for v in _DEV_VERBS)
    has_target = any(t in lowered for t in _SYSTEM_TARGETS) or "系统" in text
    has_scheme = any(k in text for k in _DESIGN_DOC_HINTS)
    has_prompt = any(k in lowered for k in ("提示词", "prompt"))

    if has_dev and has_target:
        return True
    if has_target and has_scheme:
        return True
    if has_prompt and (has_dev or has_target):
        return True
    if "管理系统" in text and has_scheme:
        return True
    if _PROJECT_NAME_RE.search(text):
        return True
    if _DEV_QUESTION_RE.search(text):
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
    if any(
        k in lowered
        for k in ("搜索", "search", "查一下", "查询资料", "网上", "百度", "google", "duckduckgo")
    ):
        return "search", "search", {"query": extract_search_query(text)}
    if any(
        k in lowered
        for k in (
            "数据库",
            "sql",
            "查询表",
            "有多少",
            "多少用户",
            "用户数",
            "会话数",
            "消息数",
            "统计",
            "audit",
            "tool_log",
        )
    ):
        return "database", "database", {"query": extract_database_query(text)}
    if any(k in lowered for k in ("文件", "读取", "上传", "file", "文档", "pdf", "excel")) or wants_file_list(text):
        return "file", "file", {"query": extract_file_query(text)}

    return "chat", "", {}


async def intent_node(state: AgentState) -> dict:
    user_input = state.get("user_input") or ""
    intent, tool_name, tool_input = detect_intent(user_input)

    if (state.get("metadata") or {}).get("enable_tools") is False and intent != "prompt_engineer":
        return {
            "intent": "chat",
            "tool_name": "",
            "tool_input": {},
            "current_node": "intent",
            "metadata": {"detected_intent": "chat", "tools_disabled": True},
        }

    return {
        "intent": intent,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "current_node": "intent",
        "metadata": {"detected_intent": intent},
    }
