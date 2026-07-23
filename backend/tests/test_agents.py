"""tests/test_agents.py — Agent 测试"""

import pytest

from app.agents.base import BaseAgent
from app.agents.coder import CoderAgent
from app.agents.analyst import AnalystAgent
from app.agents.manager import ManagerAgent
from app.core.context.state import init_state


class TestAgentRegistry:
    def test_all_agents_registered(self):
        agents = [CoderAgent(), AnalystAgent(), ManagerAgent()]
        names = {a.name for a in agents}
        assert "coder" in names
        assert "analyst" in names
        assert "manager" in names

    @pytest.mark.asyncio
    async def test_coder_agent_run(self):
        agent = CoderAgent()
        state = init_state(user_input="test")
        result = await agent.run(state)
        assert result["current_node"] == "coder"

    @pytest.mark.asyncio
    async def test_analyst_agent_run(self):
        agent = AnalystAgent()
        state = init_state(user_input="test")
        result = await agent.run(state)
        assert result["current_node"] == "analyst"