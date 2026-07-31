"""app/runtime/tools/manager.py — Tool Manager（§4.4）

统一工具执行出口：
- args_schema 运行前校验
- 单工具超时（asyncio.wait_for）
- 多 tool_calls 并行执行（asyncio.gather）
- 连续失败熔断：N 次后自动禁用并告警
- ToolStart/ToolEnd 领域事件进 EventBus（供审计/计费/评测订阅）
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.runtime.tools.plugin import BasePlugin
from app.runtime.tools.sources.builtin import BuiltinPlugin
from app.runtime.tools.sources.mcp import McpPlugin, load_mcp_server_configs
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import is_tool_enabled
from app.utils.logger import logger

CIRCUIT_BREAK_THRESHOLD = 5  # 连续失败 N 次熔断


class ToolManager:
    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._tools: dict[str, BaseTool] = {}
        self._consecutive_failures: dict[str, int] = {}
        self._circuit_broken: set[str] = set()
        self._loaded = False

    # ---------- 插件生命周期 ----------

    async def setup(self) -> None:
        """加载全部插件源：builtin 必载，MCP 按配置接入。"""
        if self._loaded:
            return
        await self.register_plugin(BuiltinPlugin())
        for server_name, config in load_mcp_server_configs().items():
            await self.register_plugin(McpPlugin(server_name, config))
        self._loaded = True

    async def register_plugin(self, plugin: BasePlugin) -> None:
        try:
            await plugin.load()
        except Exception as exc:
            logger.warning(f"[ToolManager] 插件「{plugin.manifest.name}」加载失败: {exc}")
            return
        self._plugins[plugin.manifest.name] = plugin
        for tool in plugin.list_tools():
            self._tools[tool.name] = tool

    async def unregister_plugin(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin is None:
            return
        for tool in plugin.list_tools():
            self._tools.pop(tool.name, None)
        await plugin.unload()

    # ---------- 查询 ----------

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def list_available_tools(self) -> list[BaseTool]:
        """可供 FC 绑定的工具：排除熔断与后台禁用的。"""
        return [
            t for t in self._tools.values()
            if t.name not in self._circuit_broken and is_tool_enabled(t.name)
        ]

    def function_schemas(self) -> list[dict[str, Any]]:
        return [t.to_function_schema() for t in self.list_available_tools()]

    # ---------- 执行 ----------

    async def execute(self, name: str, arguments: dict[str, Any], *, context: dict[str, Any] | None = None) -> ToolResult:
        """单工具执行：校验 → 超时保护 → 熔断计数 → 事件上报。"""
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(output="", duration_ms=0, error=f"工具未注册: {name}")
        if name in self._circuit_broken:
            return ToolResult(output="", duration_ms=0, error=f"工具已熔断（连续失败 {CIRCUIT_BREAK_THRESHOLD} 次）: {name}")
        if not is_tool_enabled(name):
            return ToolResult(output="", duration_ms=0, error=f"工具已禁用: {name}")

        kwargs = dict(arguments or {})
        for key, value in (context or {}).items():
            kwargs[f"_{key}"] = value

        validated, validation_error = tool.validate_args(kwargs)
        if validation_error:
            return ToolResult(output="", duration_ms=0, error=validation_error)

        await self._publish_event("ToolStart", {"tool": name, "arguments": arguments, **self._ctx_payload(context)})
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(tool.run(**validated), timeout=tool.timeout_s)
        except asyncio.TimeoutError:
            duration_ms = int((time.perf_counter() - started) * 1000)
            result = ToolResult(output="", duration_ms=duration_ms, error=f"工具执行超时（>{tool.timeout_s}s）")
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            result = ToolResult(output="", duration_ms=duration_ms, error=str(exc))

        self._record_outcome(name, failed=bool(result.error))
        await self._publish_event(
            "ToolEnd" if not result.error else "ToolFailed",
            {
                "tool": name,
                "arguments": arguments,
                "output": result.output,
                "durationMs": result.duration_ms,
                "error": result.error,
                **self._ctx_payload(context),
            },
        )
        return result

    async def execute_many(
        self,
        calls: list[dict[str, Any]],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[ToolResult]:
        """并行执行多个 tool_calls（模型一次返回多个调用时）。"""
        tasks = [
            self.execute(str(call.get("name") or ""), dict(call.get("args") or {}), context=context)
            for call in calls
        ]
        return list(await asyncio.gather(*tasks))

    # ---------- 熔断 ----------

    def _record_outcome(self, name: str, *, failed: bool) -> None:
        if not failed:
            self._consecutive_failures[name] = 0
            return
        count = self._consecutive_failures.get(name, 0) + 1
        self._consecutive_failures[name] = count
        if count >= CIRCUIT_BREAK_THRESHOLD:
            self._circuit_broken.add(name)
            logger.error(f"[ToolManager] 工具「{name}」连续失败 {count} 次，已熔断禁用")

    def reset_circuit(self, name: str) -> None:
        self._circuit_broken.discard(name)
        self._consecutive_failures[name] = 0

    # ---------- 事件 ----------

    @staticmethod
    def _ctx_payload(context: dict[str, Any] | None) -> dict[str, Any]:
        ctx = context or {}
        payload: dict[str, Any] = {}
        if ctx.get("user_id"):
            payload["userId"] = ctx["user_id"]
        if ctx.get("conversation_id"):
            payload["conversationId"] = ctx["conversation_id"]
        return payload

    async def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            from app.events.bus import event_bus
            from app.events.message import EventMessage

            await event_bus.publish(EventMessage(event_type=event_type, data=payload, sender="tool_manager"))
        except Exception:
            pass


_tool_manager: ToolManager | None = None


def get_tool_manager() -> ToolManager:
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager
