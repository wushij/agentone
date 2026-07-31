"""app/runtime/state/domains.py — 分域 State（§5.1）

七域设计：conversation / plan / execution / tool / memory / context / output。
新执行链路（ReAct/FC）使用分域 RuntimeState；旧图沿用扁平 AgentState，
通过 from_flat / to_flat 双向薄适配，保证任何阶段系统可运行。
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langchain_core.messages import AnyMessage

STATE_VERSION = 1


class ConversationState(TypedDict, total=False):
    session_id: str
    user_id: str
    conversation_id: str
    message_id: str
    user_input: str


class PlanState(TypedDict, total=False):
    plan_text: str
    revisions: int


class ExecutionState(TypedDict, total=False):
    current_node: str
    iterations: int
    reflections: int
    scratchpad: list[dict[str, Any]]  # 工具调用轨迹（ReAct）
    error: str


class ToolState(TypedDict, total=False):
    pending_calls: list[dict[str, Any]]
    results: list[dict[str, Any]]
    retries: int


class MemoryState(TypedDict, total=False):
    recalled: list[dict[str, Any]]


class ContextState(TypedDict, total=False):
    blocks: list[dict[str, Any]]  # 每块 {name, tokens, truncated}
    budget_total: int
    budget_used: int


class OutputState(TypedDict, total=False):
    answer: str
    confidence: float
    verdict: Literal["approved", "retry", "replan"]
    feedback: str
    tool_calls: list[dict[str, Any]]
    prompt_tokens: int
    completion_tokens: int


class RuntimeState(TypedDict, total=False):
    state_version: int
    conversation: ConversationState
    plan: PlanState
    execution: ExecutionState
    tool: ToolState
    memory: MemoryState
    context: ContextState
    output: OutputState
    messages: list[AnyMessage]
    metadata: dict[str, Any]  # 仅存路由参数（model_id/kb_ids 等），禁止堆运行时数据


# ---------- 分域 reducer ----------

def merge_domain(left: dict | None, right: dict | None) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


def append_list(left: list | None, right: list | None) -> list:
    return list(left or []) + list(right or [])


# ---------- 初始化与薄适配 ----------

def init_runtime_state(
    *,
    user_input: str,
    session_id: str = "",
    user_id: str = "",
    conversation_id: str = "",
    message_id: str = "",
    history: list[AnyMessage] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RuntimeState:
    return RuntimeState(
        state_version=STATE_VERSION,
        conversation=ConversationState(
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            user_input=user_input,
        ),
        plan=PlanState(plan_text="", revisions=0),
        execution=ExecutionState(current_node="", iterations=0, reflections=0, scratchpad=[], error=""),
        tool=ToolState(pending_calls=[], results=[], retries=0),
        memory=MemoryState(recalled=[]),
        context=ContextState(blocks=[], budget_total=0, budget_used=0),
        output=OutputState(answer="", tool_calls=[], prompt_tokens=0, completion_tokens=0),
        messages=list(history or []),
        metadata=dict(metadata or {}),
    )


def migrate_state(state: RuntimeState) -> RuntimeState:
    """checkpointer 反序列化后按 state_version 迁移，避免升级后旧会话崩溃。"""
    version = int(state.get("state_version") or 0)
    if version < 1:
        # v0 → v1：补齐缺失分域
        template = init_runtime_state(user_input=str(state.get("conversation", {}).get("user_input") or ""))
        for key, value in template.items():
            state.setdefault(key, value)  # type: ignore[misc]
        state["state_version"] = STATE_VERSION
    return state


def from_flat(flat: dict[str, Any]) -> RuntimeState:
    """旧版扁平 AgentState → 分域 RuntimeState。"""
    meta = dict(flat.get("metadata") or {})
    state = init_runtime_state(
        user_input=str(flat.get("user_input") or ""),
        session_id=str(flat.get("session_id") or ""),
        user_id=str(flat.get("user_id") or ""),
        conversation_id=str(flat.get("conversation_id") or ""),
        message_id=str(flat.get("message_id") or ""),
        history=flat.get("messages") or [],
        metadata=meta,
    )
    state["plan"]["plan_text"] = str(meta.get("plan") or "")
    state["execution"]["current_node"] = str(flat.get("current_node") or "")
    state["execution"]["error"] = str(flat.get("error") or "")
    state["output"]["answer"] = str(flat.get("final_answer") or "")
    return state


def to_flat(state: RuntimeState) -> dict[str, Any]:
    """分域 RuntimeState → 旧版扁平字段（供仍依赖旧结构的消费方使用）。"""
    conv = state.get("conversation") or {}
    execution = state.get("execution") or {}
    output = state.get("output") or {}
    scratchpad = execution.get("scratchpad") or []
    last_tool = scratchpad[-1] if scratchpad else {}
    return {
        "session_id": conv.get("session_id", ""),
        "user_id": conv.get("user_id", ""),
        "conversation_id": conv.get("conversation_id", ""),
        "message_id": conv.get("message_id", ""),
        "user_input": conv.get("user_input", ""),
        "messages": state.get("messages") or [],
        "tool_name": last_tool.get("tool", ""),
        "tool_result": last_tool.get("output", ""),
        "tool_error": last_tool.get("error", ""),
        "final_answer": output.get("answer", ""),
        "llm_response": output.get("answer", ""),
        "error": execution.get("error", ""),
        "current_node": execution.get("current_node", ""),
        "metadata": dict(state.get("metadata") or {}),
    }
