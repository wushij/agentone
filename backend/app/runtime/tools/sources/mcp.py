"""app/runtime/tools/sources/mcp.py — MCP 客户端插件源（§4.2）

一次接入 = 获得整个 MCP 生态。服务器配置存于 settings_store 的 `mcpServers` 键：
    {"mcpServers": {"fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]},
                    "remote": {"url": "http://host:port/sse"}}}
依赖官方 `mcp` SDK（可选依赖）：未安装或连接失败时优雅降级为空工具集，不阻断主链路。
"""

from __future__ import annotations

import time
from typing import Any

from app.runtime.tools.plugin import BasePlugin, PluginManifest
from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger


class McpProxyTool(BaseTool):
    """把远端 MCP tool 包装为本地 BaseTool，统一走 ToolManager 校验/超时/熔断。"""

    def __init__(self, server_name: str, tool_name: str, description: str, input_schema: dict, session: Any):
        self.name = f"mcp_{server_name}_{tool_name}"
        self.description = f"[MCP:{server_name}] {description or tool_name}"
        self._remote_name = tool_name
        self._input_schema = input_schema or {}
        self._session = session
        self.timeout_s = 60.0

    def to_function_schema(self) -> dict[str, Any]:
        parameters = self._input_schema if self._input_schema.get("type") == "object" else {
            "type": "object",
            "properties": self._input_schema.get("properties", {}),
            "required": self._input_schema.get("required", []),
        }
        return {
            "type": "function",
            "function": {"name": self.name, "description": self.description, "parameters": parameters},
        }

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        args = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        try:
            result = await self._session.call_tool(self._remote_name, arguments=args)
            parts: list[str] = []
            for item in getattr(result, "content", []) or []:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
            output = "\n".join(parts) or "(MCP 工具无文本输出)"
            duration_ms = int((time.perf_counter() - started) * 1000)
            if getattr(result, "isError", False):
                return ToolResult(output="", duration_ms=duration_ms, error=output)
            return ToolResult(output=output, duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return ToolResult(output="", duration_ms=duration_ms, error=f"MCP 调用失败: {exc}")


class McpPlugin(BasePlugin):
    """管理一个 MCP server 的连接生命周期（stdio / SSE 两种 transport）。"""

    def __init__(self, server_name: str, config: dict[str, Any]):
        self.manifest = PluginManifest(
            name=f"mcp:{server_name}",
            source="mcp",
            description=f"MCP server「{server_name}」",
            permissions=["network"],
        )
        self._server_name = server_name
        self._config = config
        self._tools: list[BaseTool] = []
        self._exit_stack: Any = None

    async def load(self) -> None:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            logger.warning(f"[MCP] 未安装 mcp SDK，跳过 server「{self._server_name}」（pip install mcp）")
            return

        from contextlib import AsyncExitStack

        self._exit_stack = AsyncExitStack()
        try:
            if self._config.get("url"):
                from mcp.client.sse import sse_client

                transport = await self._exit_stack.enter_async_context(sse_client(self._config["url"]))
            else:
                params = StdioServerParameters(
                    command=self._config.get("command", ""),
                    args=list(self._config.get("args") or []),
                    env=self._config.get("env") or None,
                )
                transport = await self._exit_stack.enter_async_context(stdio_client(params))

            read, write = transport
            session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            listing = await session.list_tools()
            self._tools = [
                McpProxyTool(
                    server_name=self._server_name,
                    tool_name=t.name,
                    description=t.description or "",
                    input_schema=dict(t.inputSchema or {}),
                    session=session,
                )
                for t in listing.tools
            ]
            logger.info(f"[MCP] server「{self._server_name}」已接入 {len(self._tools)} 个工具")
        except Exception as exc:
            logger.warning(f"[MCP] server「{self._server_name}」连接失败，已跳过: {exc}")
            await self.unload()

    async def unload(self) -> None:
        self._tools = []
        if self._exit_stack is not None:
            try:
                await self._exit_stack.aclose()
            except Exception:
                pass
            self._exit_stack = None

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools)

    async def health_check(self) -> bool:
        return bool(self._tools)


def load_mcp_server_configs() -> dict[str, dict[str, Any]]:
    """从 settings_store 读取 MCP server 配置。"""
    try:
        from app.services.system.settings_store import settings_store

        servers = settings_store.get("mcpServers", {}) or {}
        return {name: cfg for name, cfg in servers.items() if isinstance(cfg, dict)}
    except Exception:
        return {}
