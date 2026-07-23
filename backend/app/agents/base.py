"""app/agents/base.py — Agent 基类"""

from abc import ABC, abstractmethod
from typing import Any

from app.core.context.state import AgentState


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def run(self, state: AgentState) -> dict[str, Any]:
        ...