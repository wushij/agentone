"""app/agents/writer.py — Writer / Summarizer Agent

Prompt 拼装已收口至 ContextBuilder（§6.1）；
流式输出时透传 LangChain usage_metadata 实现真实 token 计量（§9.2）。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.context.state import AgentState
from app.llm.factory import create_chat_model


@dataclass
class UsageCollector:
    """收集流式输出中的真实 token 用量（usage_metadata 透传）。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    from_provider: bool = False  # True=真实值，False=估算值

    def record_chunk(self, chunk) -> None:
        usage = getattr(chunk, "usage_metadata", None)
        if usage:
            self.prompt_tokens = int(usage.get("input_tokens") or 0)
            self.completion_tokens = int(usage.get("output_tokens") or 0)
            self.from_provider = True

    def fallback_estimate(self, prompt_text_tokens: int, completion_text: str) -> None:
        """provider 未回传 usage 时，用 tokenizer 估算兜底。"""
        if self.from_provider:
            return
        from app.runtime.context.budget import count_tokens

        self.prompt_tokens = prompt_text_tokens
        self.completion_tokens = count_tokens(completion_text)


def _llm_for_state(state: AgentState):
    model_id = (state.get("metadata") or {}).get("model_id")
    return create_chat_model(model=model_id)


def _build_summarizer_messages(state: AgentState) -> list:
    """保留旧入口签名；实现委托给 ContextBuilder（唯一 Prompt 拼装出口）。"""
    from app.runtime.context.builder import get_context_builder

    messages, context_state = get_context_builder().build("summarizer", dict(state))
    # 注入明细写回 metadata，供调试面板可视化（§6.2）
    meta = state.get("metadata")
    if isinstance(meta, dict):
        meta["context_state"] = context_state
    return messages


async def stream_summarizer_tokens(state: AgentState, usage: UsageCollector | None = None):
    llm = _llm_for_state(state)
    messages = _build_summarizer_messages(state)

    chunks: list[str] = []
    async for chunk in llm.astream(messages):
        if usage is not None:
            usage.record_chunk(chunk)
        delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        if delta:
            chunks.append(delta)
            yield delta

    if usage is not None and not usage.from_provider:
        from app.runtime.context.budget import count_tokens

        prompt_tokens = sum(count_tokens(str(getattr(m, "content", "") or "")) for m in messages)
        usage.fallback_estimate(prompt_tokens, "".join(chunks))
