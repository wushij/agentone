"""app/runtime/tools/plugin.py — Plugin 抽象（§4.1）

统一的插件协议：所有工具来源（builtin / python / openapi / mcp / remote）
都以 Plugin 形式接入 ToolManager，manifest 格式为将来的插件市场预留。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.tools.base import BaseTool


@dataclass
class PluginManifest:
    name: str
    version: str = "1.0.0"
    source: str = "builtin"  # builtin / python / openapi / mcp / remote
    description: str = ""
    permissions: list[str] = field(default_factory=list)  # network / fs:read / db:read ...
    signature: str = ""


class BasePlugin(ABC):
    """插件生命周期协议：load → list_tools → health_check → unload。"""

    manifest: PluginManifest

    @abstractmethod
    async def load(self) -> None:
        ...

    @abstractmethod
    async def unload(self) -> None:
        ...

    @abstractmethod
    def list_tools(self) -> list[BaseTool]:
        ...

    async def health_check(self) -> bool:
        return True
