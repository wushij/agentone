"""backend/app/graph/nodes/summarizer_node.py"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import AgentState
from app.llm.factory import create_chat_model
from app.utils.prompt_loader import load_prompt

SUMMARIZER_PROMPT = load_prompt(
    "summary",
    "你是一个总结代理（Summary Agent / Summarizer Agent）。"
    "你需要整合任务规划、收集到的检索信息/工具执行结果以及审阅建议，"
    "为用户输出最终精美、易懂的回答。",
)


def _llm_for_state(state: AgentState):
    model_id = (state.get("metadata") or {}).get("model_id")
    return create_chat_model(model=model_id)


def _build_summarizer_messages(state: AgentState) -> list:
    user_input = state.get("user_input") or ""
    plan = (state.get("metadata") or {}).get("plan") or ""
    rag_context = (state.get("metadata") or {}).get("rag_context") or ""
    tool_name = state.get("tool_name") or ""
    tool_result = state.get("tool_result") or ""
    review = (state.get("metadata") or {}).get("review") or ""

    context = (
        f"用户问题: {user_input}\n"
        f"规划计划: {plan}\n"
        f"知识库参考: {rag_context or '（无）'}\n"
        f"调用的工具: {tool_name}\n"
        f"工具结果: {tool_result or '（无）'}\n"
        f"审核结果: {review}"
    )
    return [
        SystemMessage(content=SUMMARIZER_PROMPT),
        *state.get("messages", []),
        HumanMessage(content=context),
    ]


async def stream_summarizer_tokens(state: AgentState):
    llm = _llm_for_state(state)
    messages = _build_summarizer_messages(state)
    async for chunk in llm.astream(messages):
        delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        if delta:
            yield delta
