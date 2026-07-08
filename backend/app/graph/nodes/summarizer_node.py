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
    intent = state.get("intent") or "chat"
    if intent == "prompt_engineer":
        engineer_prompt = load_prompt(
            "prompt_engineer",
            "你是 AI 编程提示词工程专家，为用户生成企业级可投喂 AI 编程工具的开发提示词。",
        )
        context = (
            f"【用户需求】\n{user_input}\n\n"
            "请按上方规则输出完整的企业级 AI 编程开发提示词（带 emoji 分节，可直接复制给 Cursor/GPT 使用）。"
        )
        return [
            SystemMessage(content=engineer_prompt),
            HumanMessage(content=context),
        ]

    meta = state.get("metadata") or {}
    plan = meta.get("plan") or ""
    rag_context = meta.get("rag_context") or ""
    kb_ids = meta.get("kb_ids") or []
    kb_mounted = bool(kb_ids)
    tool_name = state.get("tool_name") or ""
    tool_result = state.get("tool_result") or ""
    review = meta.get("review") or ""

    if kb_mounted:
        kb_status = f"已挂载 {len(kb_ids)} 个知识库"
        if rag_context:
            kb_instruction = "有知识库参考时优先忠实转述；有工具结果时数字不得改动。"
        else:
            kb_instruction = (
                "知识库已检索但未命中相关资料，请仍用大模型正常完整作答；"
                "勿整段只回复「知识库暂无该条目」。"
            )
    else:
        kb_status = "未挂载（请基于模型知识与工具结果直接作答）"
        kb_instruction = "按常规模型能力作答即可。"

    context = (
        f"【当前用户问题】\n{user_input}\n\n"
        f"【知识库挂载状态】\n{kb_status}\n\n"
        f"【规划计划】\n{plan or '（无）'}\n\n"
        f"【知识库参考资料】\n{rag_context or '（无）'}\n\n"
        f"【调用的工具】\n{tool_name or '（无）'}\n\n"
        f"【工具结果】\n{tool_result or '（无）'}\n\n"
        f"【审核结果】\n{review or '（无）'}\n\n"
        f"请按人设 §4 排版规则输出最终回答。{kb_instruction}"
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
