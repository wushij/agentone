"""backend/app/graph/nodes/generate_node.py"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.state import AgentState
from app.llm.factory import create_chat_model
from app.utils.prompt_loader import load_prompt

TOOL_SYSTEM_PROMPT = load_prompt(
    "tool",
    "你是 AgentOne 智能体助手。用户提出了需要工具辅助的问题，"
    "工具已执行并返回结果。请基于工具结果用自然语言给出清晰、准确的最终回答。"
    "若工具执行失败，请友好说明原因并给出建议。",
)


def _llm_for_state(state: AgentState):
    model_id = (state.get("metadata") or {}).get("model_id")
    return create_chat_model(model=model_id)


def _build_tool_messages(state: AgentState) -> list:
    user_input = state.get("user_input") or ""
    tool_name = state.get("tool_name") or ""
    tool_result = state.get("tool_result") or ""
    tool_error = state.get("tool_error") or ""

    context = (
        f"用户问题：{user_input}\n"
        f"调用工具：{tool_name}\n"
        f"工具结果：{tool_result or '（无）'}\n"
        f"工具错误：{tool_error or '（无）'}"
    )
    return [
        SystemMessage(content=TOOL_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]


async def generate_node(state: AgentState) -> dict:
    if state.get("error"):
        return {"current_node": "generate"}

    llm = _llm_for_state(state)
    messages = _build_tool_messages(state)
    chunks: list[str] = []
    async for chunk in llm.astream(messages):
        delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        if delta:
            chunks.append(delta)

    answer = "".join(chunks)
    return {
        "llm_response": answer,
        "final_answer": answer,
        "messages": [AIMessage(content=answer)],
        "current_node": "generate",
    }


async def stream_generate_tokens(state: AgentState):
    llm = _llm_for_state(state)
    messages = _build_tool_messages(state)
    async for chunk in llm.astream(messages):
        delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        if delta:
            yield delta
