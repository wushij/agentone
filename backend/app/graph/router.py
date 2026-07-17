"""backend/app/graph/router.py"""

from __future__ import annotations

from typing import Literal

from app.graph.state import AgentState
from app.tools.registry import get_tool

RouteAfterResearcher = Literal["reviewer", "tool", "unsupported"]
RouteAfterTool = Literal["reviewer", "retry_tool", "error_handler"]


def route_after_researcher(state: AgentState) -> RouteAfterResearcher:
    if state.get("error"):
        return "reviewer"

    intent = state.get("intent") or "chat"
    if intent in ("chat", "prompt_engineer"):
        return "reviewer"

    tool_name = state.get("tool_name") or ""
    if get_tool(tool_name) is not None:
        return "tool"

    return "unsupported"


def route_after_tool(state: AgentState) -> RouteAfterTool:
    if state.get("error"):
        return "error_handler"
    if state.get("tool_error") and not state.get("tool_result"):
        retries = state.get("tool_retries") or 0
        max_retries = 3
        if retries < max_retries:
            return "retry_tool"
        return "error_handler"
    return "reviewer"


def route_unsupported_message(state: AgentState) -> dict:
    intent = state.get("intent") or "unknown"
    return {
        "final_answer": (
            f"识别到意图「{intent}」，但当前没有匹配的内置工具。"
            "已支持：普通对话、calculator（计算器）、search（网络搜索）、"
            "file（用户文件读取）、database（只读数据库查询）。"
        ),
        "llm_response": "",
        "error": "",
        "current_node": "unsupported",
    }


async def error_handler_node(state: AgentState) -> dict:
    message = state.get("error") or state.get("tool_error") or "执行失败，请稍后重试"
    return {
        "final_answer": message,
        "error": message,
        "current_node": "error_handler",
    }
