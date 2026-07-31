"""app/agents/manager.py — Manager / Supervisor Agent（§15.2）

多 Agent 协调者。运行时由 SupervisorLoop 实现：从 Agent Registry 按能力发现
候选专家，LLM 决策选择并委派执行。本类作为 Supervisor 的注册卡片与决策入口。
"""

from typing import Any

from app.agents.base import BaseAgent


class ManagerAgent(BaseAgent):
    name = "manager"
    description = "多 Agent 协调调度（Supervisor）"

    async def route(self, user_input: str, model_id: str | None = None) -> str:
        """按能力选择最合适的专家子 Agent，返回其名字。"""
        from app.runtime.executor.loops.supervisor import select_agent
        from app.runtime.registry import get_agent_registry

        reg = get_agent_registry()
        names = {m.name for m in reg.list()}
        picked, _reason = await select_agent(user_input, model_id, names, reg.catalog())
        return picked

    async def run(self, state: Any) -> dict[str, Any]:
        user_input = ""
        if isinstance(state, dict):
            user_input = state.get("user_input") or ""
        picked = await self.route(user_input, (state.get("metadata") or {}).get("model_id") if isinstance(state, dict) else None)
        return {
            "current_node": "manager",
            "metadata": {"agent": "manager", "delegated_to": picked},
        }
