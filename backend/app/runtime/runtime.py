"""app/runtime/runtime.py — Runtime 统一门面（§2.2 门面收口）

API 层只认 Runtime，不再直接 import engine/memory/rag。
GraphRunner 作为 Runtime 的 Executor 组件（渐进迁移：阶段 1 薄适配收口）。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.core.events.events import SseEvent
from app.utils.logger import logger


class AgentRuntime:
    """Agent Runtime 门面：Executor / ToolManager / ContextBuilder 的统一入口。"""

    def __init__(self) -> None:
        self._executor = None
        self._ready = False

    # ---------- 生命周期 ----------

    async def setup(self) -> None:
        """应用启动时调用：加载插件源（builtin/MCP）、预热执行器。"""
        if self._ready:
            return
        from app.runtime.tools.manager import get_tool_manager

        try:
            await get_tool_manager().setup()
        except Exception as exc:
            logger.warning(f"[Runtime] ToolManager 初始化失败（将在首次调用时重试）: {exc}")
        self._ready = True

    @property
    def executor(self):
        """Executor 组件（GraphRunner 迁入）。"""
        if self._executor is None:
            from app.core.engine.engine import get_engine

            self._executor = get_engine()
        return self._executor

    @property
    def tools(self):
        from app.runtime.tools.manager import get_tool_manager

        return get_tool_manager()

    @property
    def context_builder(self):
        from app.runtime.context.builder import get_context_builder

        return get_context_builder()

    # ---------- 执行入口 ----------

    async def stream_sse(self, user_input: str, **kwargs: Any) -> AsyncIterator[SseEvent]:
        await self.setup()
        async for event in self.executor.stream_sse(user_input, **kwargs):
            yield event

    async def stream_sse_encoded(self, user_input: str, **kwargs: Any) -> AsyncIterator[str]:
        async for event in self.stream_sse(user_input, **kwargs):
            yield event.encode()

    async def invoke(self, user_input: str, **kwargs: Any) -> dict[str, Any]:
        await self.setup()
        return await self.executor.invoke(user_input, **kwargs)


_runtime: AgentRuntime | None = None


def get_runtime() -> AgentRuntime:
    global _runtime
    if _runtime is None:
        _runtime = AgentRuntime()
    return _runtime
