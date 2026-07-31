"""app/runtime/executor/loops/supervisor.py — Supervisor 多 Agent 编排（§15.2）

Supervisor（Manager）从 Agent Registry 按能力发现候选专家子 Agent，
用 LLM 决策（失败回退关键词启发式）选择最合适的专家，emit AgentSwitch，
再把执行委派给该专家的 ReactLoop（绑定其受限工具集 + 注入 persona）。

SSE 事件复用既有协议：step(supervisor→agent→...) + token + tool_* + usage + done，
前端步骤面板与产物/引用渲染无需改动即可展示。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import HumanMessage

from app.core.context.state import AgentState
from app.core.events.events import SseEvent, StreamContext, done_event, error_event, step_event
from app.runtime.executor.loops.react import ReactLoop
from app.runtime.executor.tool_binding import bind_tools_if_supported
from app.runtime.registry import get_agent_registry
from app.utils.logger import logger

# 关键词启发式回退：LLM 不可用（Mock）或解析失败时按能力路由
_HEURISTICS: list[tuple[str, tuple[str, ...]]] = [
    ("coder", ("代码", "编程", "code", "函数", "脚本", "python", "算法", "bug", "debug", "计算")),
    ("analyst", ("数据", "统计", "图表", "分析", "报表", "趋势", "chart", "可视化", "占比")),
    ("researcher", ("搜索", "检索", "查一下", "最新", "资料", "新闻", "联网", "search")),
]


def _heuristic_pick(user_input: str, names: set[str]) -> str:
    text = (user_input or "").lower()
    for name, keywords in _HEURISTICS:
        if name in names and any(kw.lower() in text for kw in keywords):
            return name
    return "general" if "general" in names else next(iter(names), "general")


async def select_agent(user_input: str, model_id: str | None, names: set[str], catalog: str) -> tuple[str, str]:
    """返回 (agent_name, 决策依据)。优先 LLM 决策，异常回退启发式。"""
    try:
        from app.llm.factory import create_chat_model

        llm = create_chat_model(model=model_id)
        prompt = (
            f"用户请求：{user_input}\n\n可选专家 Agent：\n{catalog}\n\n"
            f"只回复最合适的一个专家的名字（{'/'.join(sorted(names))} 之一），不要解释。"
        )
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        picked = next((n for n in names if n.lower() in content.lower()), None)
        if picked:
            return picked, f"Supervisor 选择「{picked}」处理该请求"
    except Exception as exc:
        logger.warning(f"[Supervisor] LLM 决策失败，回退启发式路由: {exc}")
    picked = _heuristic_pick(user_input, names)
    return picked, f"按能力启发式路由至「{picked}」"


class SupervisorLoop:
    """多 Agent 路由编排；作为 async 生成器产出 SSE 事件（与 ReactLoop 同契约）。"""

    def __init__(self, runner: Any, ctx: StreamContext, state: AgentState):
        self.runner = runner
        self.ctx = ctx
        self.state = state

    async def _emit(self, node: str, status: str, **kwargs: Any) -> None:
        await self.runner._emit_status(self.ctx, node, status, **kwargs)

    def _build_bound_llm(self, manifest: Any, model_id: str | None) -> Any:
        from app.llm.factory import create_chat_model
        from app.runtime.tools.manager import get_tool_manager

        tm = get_tool_manager()
        available = tm.list_available_tools()
        if manifest.tools:
            wanted = set(manifest.tools)
            subset = [t for t in available if t.name in wanted]
        else:
            subset = available
        llm = create_chat_model(model=model_id, thinking_level=str((self.state.get("metadata") or {}).get("thinking_level") or "standard"))
        return bind_tools_if_supported(llm, subset) or llm

    async def run(self) -> AsyncIterator[SseEvent]:
        ctx = self.ctx
        state = self.state
        meta = state.get("metadata") or {}
        model_id = meta.get("model_id")
        user_input = state.get("user_input") or ""

        registry = get_agent_registry()
        manifests = registry.list()
        names = {m.name for m in manifests}
        if not names:
            yield error_event(ctx, "NO_AGENT", "Agent Registry 为空")
            yield done_event(ctx, "error")
            return

        # 1) Supervisor 决策
        yield step_event(ctx, "supervisor", "running", detail="分析请求，选择合适的专家 Agent")
        await self._emit("supervisor", "running")
        agent_name, reason = await select_agent(user_input, model_id, names, registry.catalog())
        manifest = registry.get(agent_name) or registry.get("general")
        yield step_event(ctx, "supervisor", "success", detail=reason, tool=agent_name)
        await self._emit("supervisor", "success", detail=reason, tool=agent_name)

        # 2) AgentSwitch：记录被委派的专家（写入 metadata，供审计/前端）
        if isinstance(state.get("metadata"), dict):
            state["metadata"]["active_agent"] = manifest.name
            state["metadata"]["agent_reason"] = reason
        yield step_event(ctx, "agent", "running", detail=f"由「{manifest.description}」处理", tool=manifest.name)
        await self._emit("agent", "running", tool=manifest.name)

        # 3) 委派给专家子 Agent 的 ReactLoop（受限工具 + persona）
        try:
            llm_bound = self._build_bound_llm(manifest, model_id)
            loop = ReactLoop(self.runner, ctx, state, llm_bound, persona=manifest.persona)
            async for event in loop.run():
                yield event
        except Exception as exc:
            logger.error(f"[Supervisor] 子 Agent 执行失败: {exc}", exc_info=True)
            yield error_event(ctx, "SUB_AGENT_FAILED", str(exc))
            yield done_event(ctx, "error")
