"""app/core/state.py"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage, BaseMessage


def merge_metadata(left: dict[str, Any] | None, right: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = dict(left or {})
    merged.update(right or {})
    return merged


IntentType = Literal[
    "chat", "calculator", "search", "database", "file", "prompt_engineer", "unknown"
]


class AgentState(TypedDict, total=False):
    session_id: str
    user_id: str
    conversation_id: str
    message_id: str

    messages: Annotated[list[AnyMessage], operator.add]
    user_input: str

    intent: IntentType
    tool_name: str
    tool_input: dict[str, Any]
    tool_result: str
    tool_error: str
    tool_retries: int

    llm_response: str
    final_answer: str
    error: str

    current_node: str
    metadata: Annotated[dict[str, Any], merge_metadata]


def init_state(
    *,
    user_input: str,
    session_id: str = "",
    user_id: str = "",
    conversation_id: str = "",
    message_id: str = "",
    history: list[BaseMessage] | None = None,
) -> AgentState:
    return AgentState(
        session_id=session_id,
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        messages=list(history or []),
        user_input=user_input,
        intent="chat",
        tool_name="",
        tool_input={},
        tool_result="",
        tool_error="",
        tool_retries=0,
        llm_response="",
        final_answer="",
        error="",
        current_node="",
        metadata={},
    )