"""app/agents/manager.py — Manager Agent"""

from typing import Any

from app.agents.base import BaseAgent
from app.core.context.state import AgentState


class ManagerAgent(BaseAgent):
    name = "manager"
    description = "多 Agent 协调管理 Agent"

    async def run(self, state: AgentState) -> dict[str, Any]:
        return {"current_node": "manager", "metadata": {"agent": "manager"}}