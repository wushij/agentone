"""app/agents/reviewer.py — Reviewer Agent"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.context.state import AgentState
from app.llm.factory import create_chat_model

REVIEWER_PROMPT = (
    "你是一个结果审阅代理（Reviewer Agent）。"
    "你需要审查收集到的信息和工具执行结果是否能够准确解答用户的问题。"
    "如果结果正确，请输出 'APPROVED' 以及简要说明；如果结果有误或不完整，请说明具体问题。"
)


async def reviewer_node(state: AgentState) -> dict:
    user_input = state.get("user_input") or ""
    tool_name = state.get("tool_name") or ""
    tool_result = state.get("tool_result") or ""
    tool_error = state.get("tool_error") or ""
    plan = (state.get("metadata") or {}).get("plan") or ""

    context = (
        f"用户问题: {user_input}\n"
        f"规划步骤: {plan}\n"
        f"执行工具: {tool_name}\n"
        f"工具返回结果: {tool_result or '（无）'}\n"
        f"工具报错信息: {tool_error or '（无）'}"
    )

    model_id = (state.get("metadata") or {}).get("model_id")
    llm = create_chat_model(model=model_id)

    messages = [
        SystemMessage(content=REVIEWER_PROMPT),
        HumanMessage(content=context),
    ]

    response = await llm.ainvoke(messages)
    review_content = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "current_node": "reviewer",
        "metadata": {"review": review_content},
    }