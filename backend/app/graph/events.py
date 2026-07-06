"""backend/app/graph/events.py"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

SseEventType = Literal["token", "tool_start", "tool_end", "usage", "done", "error"]


@dataclass
class StreamContext:
    conversation_id: str
    message_id: str
    user_id: str = ""


@dataclass
class SseEvent:
    event: SseEventType
    data: dict[str, Any]

    def encode(self) -> str:
        payload = json.dumps(self.data, ensure_ascii=False)
        return f"event: {self.event}\ndata: {payload}\n\n"


@dataclass
class AgentStatusEvent:
    conversation_id: str
    node: str
    status: Literal["pending", "running", "success", "error"]
    tool: str = ""
    elapsed_ms: int = 0
    error: str = ""


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def token_event(ctx: StreamContext, delta: str) -> SseEvent:
    return SseEvent(
        "token",
        {"conversationId": ctx.conversation_id, "messageId": ctx.message_id, "delta": delta},
    )


def tool_start_event(ctx: StreamContext, tool: str, tool_input: dict[str, Any]) -> SseEvent:
    return SseEvent(
        "tool_start",
        {
            "conversationId": ctx.conversation_id,
            "messageId": ctx.message_id,
            "tool": tool,
            "input": tool_input,
        },
    )


def tool_end_event(
    ctx: StreamContext,
    tool: str,
    output: str,
    duration_ms: int,
    *,
    error: str = "",
) -> SseEvent:
    data: dict[str, Any] = {
        "conversationId": ctx.conversation_id,
        "messageId": ctx.message_id,
        "tool": tool,
        "output": output,
        "durationMs": duration_ms,
    }
    if error:
        data["error"] = error
    return SseEvent("tool_end", data)


def usage_event(ctx: StreamContext, usage: TokenUsage) -> SseEvent:
    return SseEvent(
        "usage",
        {
            "conversationId": ctx.conversation_id,
            "messageId": ctx.message_id,
            "promptTokens": usage.prompt_tokens,
            "completionTokens": usage.completion_tokens,
            "totalTokens": usage.total_tokens,
        },
    )


def done_event(ctx: StreamContext, finish_reason: str = "stop") -> SseEvent:
    return SseEvent(
        "done",
        {
            "conversationId": ctx.conversation_id,
            "messageId": ctx.message_id,
            "finishReason": finish_reason,
        },
    )


def error_event(ctx: StreamContext, code: str, message: str) -> SseEvent:
    return SseEvent(
        "error",
        {
            "conversationId": ctx.conversation_id,
            "messageId": ctx.message_id,
            "code": code,
            "message": message,
        },
    )
