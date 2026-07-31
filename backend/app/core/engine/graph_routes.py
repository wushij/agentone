"""app/core/engine/graph_routes.py — LangGraph 节点路由与条件切换"""

from __future__ import annotations

from typing import Any
from langgraph.graph import END


def route_after_researcher(state: dict[str, Any]) -> str:
    """根据意图决定 Researcher 节点后的流向"""
    intent = state.get("intent", "")
    if intent in ("weather", "search", "rag", "database", "calc"):
        return "tool"
    return "writer"


def route_after_tool(state: dict[str, Any]) -> str:
    """根据工具执行结果与重试次数决定流向"""
    if state.get("error"):
        tool_attempts = state.get("tool_attempts", 0)
        if tool_attempts < 2:
            return "tool"
        return "reviewer"
    return "reviewer"
