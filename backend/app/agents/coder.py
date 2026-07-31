"""app/agents/coder.py — Coder Agent（§15.1）

代码编写/执行专家。能力与工具（python_executor/calculator）由 Agent Registry
声明；多步执行经 SupervisorLoop 委派至 ReactLoop（绑定 manifest.tools + persona）。
"""

from typing import Any

from app.agents.base import BaseAgent


class CoderAgent(BaseAgent):
    name = "coder"
    description = "代码编写、执行与自测"

    async def run(self, state: Any) -> dict[str, Any]:
        return {
            "current_node": "coder",
            "metadata": {
                "agent": "coder",
                "capabilities": self.capabilities,
                "tools": self.tools,
            },
        }
