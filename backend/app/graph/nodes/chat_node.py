"""backend/app/graph/nodes/chat_node.py"""

from __future__ import annotations

from langchain_core.messages import AIMessage, SystemMessage

from app.graph.state import AgentState
from app.llm.factory import create_chat_model
from app.utils.prompt_loader import load_prompt

SYSTEM_PROMPT = load_prompt(
    "system",
    "你是 AgentOne 企业级 AI 智能体助手。回答应简洁、准确、专业。使用中文回复，除非用户明确要求其他语言。",
)


def _llm_for_state(state: AgentState):
    model_id = (state.get("metadata") or {}).get("model_id")
    return create_chat_model(model=model_id)


async def chat_node(state: AgentState) -> dict:
    if state.get("error"):
        return {"current_node": "chat"}

    llm = _llm_for_state(state)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state.get("messages", [])]

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
        "current_node": "chat",
    }


async def stream_chat_tokens(state: AgentState):
    llm = _llm_for_state(state)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state.get("messages", [])]
    async for chunk in llm.astream(messages):
        delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        if delta:
            yield delta
