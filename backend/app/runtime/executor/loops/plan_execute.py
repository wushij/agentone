"""app/runtime/executor/loops/plan_execute.py — Plan-and-Execute（§16.1）

先由 LLM 生成结构化计划（有序子任务），再逐步执行：每步用 FC 决定并调用工具，
把已完成步骤的结果作为上下文喂给下一步；任一步失败触发一次 replan；
最后基于全部步骤结果流式总结。SSE 事件复用既有协议。
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from app.core.context.state import AgentState
from app.core.events.events import (
    SseEvent,
    StreamContext,
    TokenUsage,
    artifact_event,
    done_event,
    error_event,
    step_event,
    token_event,
    tool_end_event,
    tool_start_event,
    usage_event,
)
from app.runtime.executor.tool_binding import accumulate_usage, extract_tool_calls
from app.utils.logger import logger

MAX_STEPS = 6
MAX_REPLANS = 1


def _parse_plan(content: str) -> list[str]:
    """从 LLM 输出解析计划步骤：优先 JSON 数组，回退按行/编号切分。"""
    match = re.search(r"\[[\s\S]*\]", content)
    if match:
        try:
            arr = json.loads(match.group(0))
            steps = [str(x).strip() for x in arr if str(x).strip()]
            if steps:
                return steps[:MAX_STEPS]
        except Exception:
            pass
    lines = [re.sub(r"^\s*(\d+[\.、)]|[-*])\s*", "", ln).strip() for ln in content.splitlines()]
    steps = [ln for ln in lines if ln]
    return steps[:MAX_STEPS] if steps else []


class PlanExecuteLoop:
    """结构化计划驱动执行；async 生成器产出 SSE 事件（与 ReactLoop 同契约）。"""

    def __init__(self, runner: Any, ctx: StreamContext, state: AgentState, llm_with_tools: Any, plain_llm: Any):
        self.runner = runner
        self.ctx = ctx
        self.state = state
        self.llm_with_tools = llm_with_tools  # 已绑定工具（执行步用）
        self.plain_llm = plain_llm            # 未绑定（规划/总结用）
        self.usage_totals: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0}
        self.scratchpad: list[dict[str, Any]] = []

    async def _emit(self, node: str, status: str, **kwargs: Any) -> None:
        await self.runner._emit_status(self.ctx, node, status, **kwargs)

    def _tool_context(self) -> dict[str, Any]:
        meta = self.state.get("metadata") or {}
        return {
            "user_id": self.state.get("user_id"),
            "conversation_id": self.state.get("conversation_id"),
            "hitl": bool(meta.get("hitl")),
            "task_id": meta.get("task_id"),
        }

    async def _make_plan(self, user_input: str) -> list[str]:
        prompt = (
            f"请把以下任务拆解为 2-{MAX_STEPS} 个有序、可执行的子任务步骤。\n"
            f"任务：{user_input}\n\n"
            '只输出一个 JSON 字符串数组，例如 ["查询数据", "计算汇总", "生成图表"]，不要额外解释。'
        )
        try:
            resp = await self.plain_llm.ainvoke([HumanMessage(content=prompt)])
            accumulate_usage(resp, self.usage_totals)
            content = resp.content if isinstance(resp.content, str) else str(resp.content)
            plan = _parse_plan(content)
            return plan or [user_input]
        except Exception as exc:
            logger.warning(f"[PlanExecute] 生成计划失败，退化为单步: {exc}")
            return [user_input]

    async def _run_step(self, ctx: StreamContext, base_messages: list[BaseMessage], step_desc: str, done_summary: str) -> AsyncIterator[SseEvent]:
        messages: list[BaseMessage] = list(base_messages)
        messages.append(HumanMessage(content=(
            f"整体任务分解执行中。已完成：\n{done_summary or '（无）'}\n\n"
            f"现在只完成当前子任务：{step_desc}\n如需工具请调用；完成后简述结果。"
        )))
        resp = await self.llm_with_tools.ainvoke(messages)
        accumulate_usage(resp, self.usage_totals)
        tool_calls = extract_tool_calls(resp)

        if not tool_calls:
            text = resp.content if isinstance(resp.content, str) else str(resp.content)
            self.scratchpad.append({"step": step_desc, "output": text, "error": ""})
            return

        from app.runtime.tools.manager import get_tool_manager

        for call in tool_calls:
            yield tool_start_event(ctx, call["name"], call["args"])
        results = await get_tool_manager().execute_many(tool_calls, context=self._tool_context())
        for call, result in zip(tool_calls, results):
            self.scratchpad.append({
                "step": step_desc, "tool": call["name"],
                "output": result.output, "error": result.error,
            })
            if result.error:
                yield tool_end_event(ctx, call["name"], "", result.duration_ms, error=result.error)
            else:
                yield tool_end_event(ctx, call["name"], result.output, result.duration_ms)
                if result.artifact:
                    from app.runtime.artifacts import get_artifact_manager

                    uid = self.state.get("user_id")
                    registered = get_artifact_manager().register(
                        user_id=int(uid) if uid else None,
                        type=str(result.artifact.get("type") or "markdown"),
                        title=str(result.artifact.get("title") or ""),
                        content=str(result.artifact.get("content") or ""),
                        language=result.artifact.get("language"),
                        conversation_id=self.state.get("conversation_id"),
                        message_id=ctx.message_id,
                    )
                    if registered:
                        yield artifact_event(ctx, registered)

    def _summary_text(self) -> str:
        lines = []
        for i, e in enumerate(self.scratchpad, 1):
            status = "失败" if e.get("error") else "完成"
            lines.append(f"[{i}] {e.get('step')} → {status}: {(e.get('error') or e.get('output') or '')[:300]}")
        return "\n".join(lines)

    async def run(self) -> AsyncIterator[SseEvent]:
        from app.runtime.context.builder import get_context_builder

        ctx = self.ctx
        state = self.state
        user_input = state.get("user_input") or ""

        base_messages, _ctx_state = get_context_builder().build("react_agent", dict(state))

        # 1) 规划
        yield step_event(ctx, "planner", "running", detail="拆解任务为结构化计划")
        await self._emit("planner", "running")
        plan = await self._make_plan(user_input)
        yield step_event(ctx, "planner", "success", detail="计划：" + " → ".join(plan))
        await self._emit("planner", "success", detail=f"{len(plan)} 步计划")

        # 2) 逐步执行（失败触发一次 replan）
        replans = 0
        try:
            idx = 0
            while idx < len(plan):
                step_desc = plan[idx]
                yield step_event(ctx, "agent", "running", detail=f"第 {idx+1}/{len(plan)} 步：{step_desc}")
                await self._emit("agent", "running", detail=step_desc)
                before = len(self.scratchpad)
                async for ev in self._run_step(ctx, base_messages, step_desc, self._summary_text()):
                    yield ev
                step_failed = any(e.get("error") for e in self.scratchpad[before:])
                yield step_event(ctx, "agent", "error" if step_failed else "success",
                                 detail=f"第 {idx+1} 步{'失败' if step_failed else '完成'}")

                if step_failed and replans < MAX_REPLANS:
                    replans += 1
                    yield step_event(ctx, "planner", "running", detail="步骤失败，重新规划剩余任务")
                    remaining = await self._make_plan(f"{user_input}\n已知失败：{self._summary_text()}")
                    plan = plan[: idx + 1] + remaining
                    yield step_event(ctx, "planner", "success", detail="已重新规划")
                idx += 1

            # 3) 总结
            yield step_event(ctx, "summarizer", "running")
            await self._emit("summarizer", "running")
            summary_prompt = (
                f"任务：{user_input}\n\n各步骤执行结果：\n{self._summary_text()}\n\n"
                "请基于以上结果，给出面向用户的完整最终回答。"
            )
            chunks: list[str] = []
            try:
                async for chunk in self.plain_llm.astream([HumanMessage(content=summary_prompt)]):
                    delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                    if delta:
                        chunks.append(delta)
                        yield token_event(ctx, delta)
            except Exception:
                resp = await self.plain_llm.ainvoke([HumanMessage(content=summary_prompt)])
                text = resp.content if isinstance(resp.content, str) else str(resp.content)
                chunks.append(text)
                yield token_event(ctx, text)

            state["final_answer"] = "".join(chunks)
            yield step_event(ctx, "summarizer", "success", detail="回答生成完成")
            await self._emit("summarizer", "success")
            yield usage_event(ctx, TokenUsage(
                prompt_tokens=self.usage_totals["prompt_tokens"],
                completion_tokens=self.usage_totals["completion_tokens"],
            ))
            yield done_event(ctx, "stop")
        except Exception as exc:
            logger.error(f"[PlanExecute] 执行失败: {exc}", exc_info=True)
            yield error_event(ctx, "PLAN_EXECUTE_FAILED", str(exc))
            yield done_event(ctx, "error")
