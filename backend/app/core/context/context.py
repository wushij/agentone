"""app/core/context.py — 上下文管理"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    session_id: str = ""
    user_id: str = ""
    conversation_id: str = ""
    message_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    kb_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "metadata": self.metadata,
            "kb_ids": self.kb_ids,
        }