"""app/core — Agent 核心引擎"""

from app.core.context.state import AgentState, IntentType, init_state
from app.core.context.context import AgentContext
from app.core.events.events import (
    AgentStatusEvent,
    NODE_LABELS,
    SseEvent,
    StreamContext,
    TokenUsage,
    done_event,
    error_event,
    step_event,
    token_event,
    tool_end_event,
    tool_start_event,
    usage_event,
)


def __getattr__(name: str):
    # 惰性导出 engine，避免 planner → core → engine → planner 循环导入
    if name in ("GraphRunner", "get_engine"):
        from app.core.engine.engine import GraphRunner, get_engine

        return {"GraphRunner": GraphRunner, "get_engine": get_engine}[name]
    raise AttributeError(f"module 'app.core' has no attribute {name!r}")

__all__ = [
    "GraphRunner",
    "get_engine",
    "AgentState",
    "IntentType",
    "init_state",
    "AgentContext",
    "AgentStatusEvent",
    "NODE_LABELS",
    "SseEvent",
    "StreamContext",
    "TokenUsage",
    "done_event",
    "error_event",
    "step_event",
    "token_event",
    "tool_end_event",
    "tool_start_event",
    "usage_event",
]