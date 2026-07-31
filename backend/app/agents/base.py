"""app/agents/base.py — Agent 基类（§15.1）

Agent 是「注册卡片 + 执行契约」：name/description/manifest 描述能力，
实际多步执行由 runtime 的 SupervisorLoop + ReactLoop 驱动（绑定 manifest.tools）。
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    @property
    def manifest(self):
        """从 Agent Registry 取本 Agent 的能力清单（capabilities/tools/persona）。"""
        from app.runtime.registry import get_agent_registry

        return get_agent_registry().get(self.name)

    @property
    def capabilities(self) -> list[str]:
        m = self.manifest
        return list(m.capabilities) if m else []

    @property
    def tools(self) -> list[str]:
        m = self.manifest
        return list(m.tools) if m else []

    @abstractmethod
    async def run(self, state: Any) -> dict[str, Any]:
        ...
