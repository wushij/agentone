"""app/agents/coder.py — Coder Agent"""

from typing import Any

from app.agents.base import BaseAgent
from app.core.context.state import AgentState


class CoderAgent(BaseAgent):
    name = "coder"
    description = "代码编写与生成 Agent"

    async def run(self, state: AgentState) -> dict[str, Any]:
        return {"current_node": "coder", "metadata": {"agent": "coder"}}