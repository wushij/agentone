"""backend/app/graph/builder.py — 构建可运行的 LangGraph StateGraph"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.checkpoint import create_checkpointer
from app.graph.nodes.intent_node import intent_node
from app.graph.nodes.planner_node import planner_node
from app.graph.nodes.reviewer_node import reviewer_node
from app.graph.nodes.tool_node import tool_node
from app.graph.router import (
    error_handler_node,
    route_after_researcher,
    route_after_tool,
    route_unsupported_message,
)
from app.graph.state import AgentState


async def unsupported_node(state: AgentState) -> dict:
    return route_unsupported_message(state)


def build_graph():
    graph = StateGraph(AgentState)

    # 注册多代理节点
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", intent_node)
    graph.add_node("tool", tool_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("unsupported", unsupported_node)
    graph.add_node("error_handler", error_handler_node)

    # 编排工作流边
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")

    graph.add_conditional_edges(
        "researcher",
        route_after_researcher,
        {
            "reviewer": "reviewer",
            "tool": "tool",
            "unsupported": "unsupported",
        },
    )

    graph.add_conditional_edges(
        "tool",
        route_after_tool,
        {
            "reviewer": "reviewer",
            "retry_tool": "tool",
            "error_handler": "error_handler",
        },
    )

    graph.add_edge("reviewer", END)
    graph.add_edge("unsupported", END)
    graph.add_edge("error_handler", END)

    return graph.compile(checkpointer=create_checkpointer())


@lru_cache
def get_compiled_graph():
    return build_graph()
