"""app/runtime/tools/sources/builtin.py — 内置工具插件源（现有 4 个工具迁入）"""

from __future__ import annotations

from app.runtime.tools.plugin import BasePlugin, PluginManifest
from app.tools.base import BaseTool
from app.tools.registry import list_builtin_tools


class BuiltinPlugin(BasePlugin):
    """包装 app/tools/registry 的内置工具集，作为第一个插件源。"""

    def __init__(self) -> None:
        self.manifest = PluginManifest(
            name="builtin",
            source="builtin",
            description="AgentOne 内置工具：calculator / search / file / database",
            permissions=["network", "fs:read", "db:read"],
        )
        self._tools: list[BaseTool] = []

    async def load(self) -> None:
        self._tools = list_builtin_tools()

    async def unload(self) -> None:
        self._tools = []

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools)
