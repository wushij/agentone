"""tests/test_tools.py — Tool 测试"""

from app.tools.registry import get_tool, list_tools, list_builtin_tools


class TestToolRegistry:
    def test_list_tools(self):
        tools = list_tools()
        assert "calculator" in tools
        assert "search" in tools
        assert "file" in tools
        assert "database" in tools

    def test_get_tool(self):
        tool = get_tool("calculator")
        assert tool is not None
        assert tool.name == "calculator"

    def test_get_nonexistent_tool(self):
        tool = get_tool("nonexistent")
        assert tool is None

    def test_list_builtin_tools(self):
        tools = list_builtin_tools()
        assert len(tools) >= 4