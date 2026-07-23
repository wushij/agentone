"""app/agents/analyst.py — Analyst Agent"""

from typing import Any

from app.agents.base import BaseAgent
from app.core.context.state import AgentState


class AnalystAgent(BaseAgent):
    name = "analyst"
    description = "数据分析 Agent"

    async def run(self, state: AgentState) -> dict[str, Any]:
        return {"current_node": "analyst", "metadata": {"agent": "analyst"}}