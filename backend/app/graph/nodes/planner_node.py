"""backend/app/graph/nodes/planner_node.py"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import AgentState
from app.llm.factory import create_chat_model
from app.utils.prompt_loader import load_prompt

PLANNER_PROMPT = load_prompt(
    "planner",
    "你是一个任务规划代理（Planner Agent）。"
    "分析用户的输入，判断要解决这个问题需要哪些步骤，并生成一个简洁明了的步骤规划。",
)


async def planner_node(state: AgentState) -> dict:
    user_input = state.get("user_input") or ""
    model_id = (state.get("metadata") or {}).get("model_id")
    llm = create_chat_model(model=model_id)

    messages = [
        SystemMessage(content=PLANNER_PROMPT),
        HumanMessage(content=f"用户输入: {user_input}"),
    ]

    response = await llm.ainvoke(messages)
    plan = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "current_node": "planner",
        "metadata": {"plan": plan},
    }
