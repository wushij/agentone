"""app/agents/analyst.py — Analyst Agent（§15.1）

数据分析专家。能力与工具（database/chart/calculator）由 Agent Registry 声明；
多步执行经 SupervisorLoop 委派至 ReactLoop（绑定 manifest.tools + persona）。
"""

from typing import Any

from app.agents.base import BaseAgent


class AnalystAgent(BaseAgent):
    name = "analyst"
    description = "数据查询、统计与可视化"

    async def run(self, state: Any) -> dict[str, Any]:
        return {
            "current_node": "analyst",
            "metadata": {
                "agent": "analyst",
                "capabilities": self.capabilities,
                "tools": self.tools,
            },
        }
