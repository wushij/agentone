"""app/runtime/executor/loops/react.py — ReAct 多步循环（§3.2 §3.3）

agent(LLM FC 决策) ──tool_calls──► ToolManager(并行) ──ToolMessage 回填──► agent
        │                                                        ▲
        └──无需工具/已有答案──► reviewer ──approved──► summarizer  │
                                  └──retry/replan(≤2)─────────────┘
        └──超出 max_iterations(10) ──► 强制收敛总结

SSE 事件与前端既有协议完全兼容：step(planner/researcher/tool/reviewer/summarizer)
+ tool_start/tool_end + token + usage + done。
"""

from __future__ import annotations

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

MAX_ITERATIONS = 10
MAX_REFLECTIONS = 2


def _format_scratchpad(scratchpad: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, entry in enumerate(scratchpad, 1):
        status = "失败" if entry.get("error") else "成功"
        lines.append(
            f"[{i}] {entry.get('tool')}({entry.get('args')}) → {status}: "
            f"{(entry.get('error') or entry.get('output') or '')[:500]}"
        )
    return "\n".join(lines)


class ReactLoop:
    """FC 驱动的多步执行循环；作为 async 生成器产出 SSE 事件。"""

    def __init__(self, runner: Any, ctx: StreamContext, state: AgentState, llm_with_tools: Any, *, persona: str = ""):
        self.runner = runner  # GraphRunner：复用 _emit_status（审计/WS 通知）
        self.ctx = ctx
        self.state = state
        self.llm_with_tools = llm_with_tools
        self.persona = persona  # 子 Agent 人设（§15）：非空时作为 SystemMessage 前置
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

    def _register_artifact(self, artifact: dict[str, Any] | None) -> dict[str, Any] | None:
        """工具产出 Artifact 时登记入库，返回含 id 的精简 dict。"""
        if not artifact:
            return None
        try:
            from app.runtime.artifacts import get_artifact_manager

            user_id = self.state.get("user_id")
            return get_artifact_manager().register(
                user_id=int(user_id) if user_id else None,
                type=str(artifact.get("type") or "markdown"),
                title=str(artifact.get("title") or ""),
                content=str(artifact.get("content") or ""),
                language=artifact.get("language"),
                conversation_id=self.state.get("conversation_id"),
                message_id=self.ctx.message_id,
            )
        except Exception:
            return None

    async def _decide(self, messages: list[BaseMessage]) -> AIMessage:
        response = await self.llm_with_tools.ainvoke(messages)
        accumulate_usage(response, self.usage_totals)
        return response

    async def run(self) -> AsyncIterator[SseEvent]:
        from app.runtime.context.builder import get_context_builder
        from app.runtime.tools.manager import get_tool_manager

        ctx = self.ctx
        state = self.state
        tool_manager = get_tool_manager()

        # planner/researcher 步（FC 模式下由模型自主决策，保持前端步骤面板兼容）
        yield step_event(ctx, "planner", "success", detail="Function Calling 模式：模型自主规划与工具决策")
        await self._emit("planner", "success", detail="FC 自主决策")
        yield step_event(ctx, "researcher", "running")

        base_messages, context_state = get_context_builder().build("react_agent", dict(state))
        meta = state.get("metadata")
        if isinstance(meta, dict):
            meta["context_state"] = context_state
        loop_messages: list[BaseMessage] = list(base_messages)
        # 子 Agent 人设前置（§15 多 Agent）：以 SystemMessage 注入专家角色
        if self.persona:
            from langchain_core.messages import SystemMessage

            loop_messages.insert(0, SystemMessage(content=self.persona))

        yield step_event(ctx, "researcher", "success", detail="识别意图：Function Calling 自主决策")
        await self._emit("researcher", "success", detail="FC 自主决策")

        iterations = 0
        reflections = 0
        tools_used = False

        try:
            while iterations < MAX_ITERATIONS:
                iterations += 1
                response = await self._decide(loop_messages)
                tool_calls = extract_tool_calls(response)

                if not tool_calls:
                    # 无需（更多）工具：进入审阅/总结
                    break

                tools_used = True
                loop_messages.append(response)

                # 并行执行本轮全部 tool_calls（§3.2）
                started = time.perf_counter()
                for call in tool_calls:
                    yield step_event(ctx, "tool", "running", tool=call["name"])
                    yield tool_start_event(ctx, call["name"], call["args"])
                    await self._emit("tool", "running", tool=call["name"])

                results = await tool_manager.execute_many(tool_calls, context=self._tool_context())
                elapsed = int((time.perf_counter() - started) * 1000)

                for call, result in zip(tool_calls, results):
                    entry = {
                        "tool": call["name"],
                        "args": call["args"],
                        "output": result.output,
                        "error": result.error,
                        "duration_ms": result.duration_ms,
                    }
                    self.scratchpad.append(entry)
                    if result.error:
                        yield tool_end_event(ctx, call["name"], "", result.duration_ms, error=result.error)
                        yield step_event(ctx, "tool", "error", tool=call["name"], error=result.error, elapsed_ms=elapsed)
                        await self._emit("tool", "error", tool=call["name"], error=result.error)
                    else:
                        yield tool_end_event(ctx, call["name"], result.output, result.duration_ms)
                        yield step_event(
                            ctx, "tool", "success", tool=call["name"],
                            elapsed_ms=elapsed, detail=(result.output or "")[:300],
                        )
                        await self._emit("tool", "success", tool=call["name"])
                        if result.artifact:
                            registered = self._register_artifact(result.artifact)
                            if registered:
                                yield artifact_event(ctx, registered)
                    loop_messages.append(
                        ToolMessage(
                            content=(result.error and f"工具执行失败: {result.error}") or result.output or "(空输出)",
                            tool_call_id=call["id"],
                        )
                    )

            # ---------- 反思闭环（§3.3）：仅在用过工具时审阅 ----------
            last_success = next((e for e in reversed(self.scratchpad) if not e.get("error")), None)
            state["tool_name"] = str((last_success or {}).get("tool") or "")
            state["tool_result"] = str((last_success or {}).get("output") or "")
            state["tool_error"] = "" if last_success else str(
                (self.scratchpad[-1].get("error") if self.scratchpad else "") or ""
            )
            state_meta = state.setdefault("metadata", {})
            state_meta["scratchpad_text"] = _format_scratchpad(self.scratchpad)
            state_meta["iterations"] = iterations

            if tools_used:
                while True:
                    yield step_event(ctx, "reviewer", "running")
                    from app.agents.reviewer import reviewer_node

                    review_update = await reviewer_node(state)
                    state_meta.update(review_update.get("metadata") or {})
                    verdict = str(state_meta.get("review_verdict") or "approved")
                    review_text = str(state_meta.get("review") or "审阅通过")
                    yield step_event(ctx, "reviewer", "success", detail=review_text[:300])
                    await self._emit("reviewer", "success", detail=verdict)

                    if verdict == "approved" or reflections >= MAX_REFLECTIONS or iterations >= MAX_ITERATIONS:
                        break
                    # retry/replan：把反馈回填进循环，再给模型一次机会（反思回边）
                    reflections += 1
                    loop_messages.append(
                        HumanMessage(content=f"审阅未通过（{verdict}）：{review_text}\n请修正后继续。")
                    )
                    response = await self._decide(loop_messages)
                    tool_calls = extract_tool_calls(response)
                    if not tool_calls:
                        break
                    iterations += 1
                    loop_messages.append(response)
                    for call in tool_calls:
                        yield tool_start_event(ctx, call["name"], call["args"])
                    results = await tool_manager.execute_many(tool_calls, context=self._tool_context())
                    for call, result in zip(tool_calls, results):
                        entry = {
                            "tool": call["name"], "args": call["args"],
                            "output": result.output, "error": result.error,
                            "duration_ms": result.duration_ms,
                        }
                        self.scratchpad.append(entry)
                        if result.error:
                            yield tool_end_event(ctx, call["name"], "", result.duration_ms, error=result.error)
                        else:
                            yield tool_end_event(ctx, call["name"], result.output, result.duration_ms)
                        loop_messages.append(
                            ToolMessage(
                                content=result.error or result.output or "(空输出)",
                                tool_call_id=call["id"],
                            )
                        )
                    last_success = next((e for e in reversed(self.scratchpad) if not e.get("error")), None)
                    state["tool_name"] = str((last_success or {}).get("tool") or "")
                    state["tool_result"] = str((last_success or {}).get("output") or "")
                    state_meta["scratchpad_text"] = _format_scratchpad(self.scratchpad)
            else:
                yield step_event(ctx, "reviewer", "success", detail="纯对话，无需审阅")

            # ---------- summarizer 流式总结（真实 token 透传） ----------
            yield step_event(ctx, "summarizer", "running")
            await self._emit("summarizer", "running")

            from app.agents.writer import UsageCollector, stream_summarizer_tokens

            collector = UsageCollector()
            chunks: list[str] = []
            async for delta in stream_summarizer_tokens(state, usage=collector):
                chunks.append(delta)
                yield token_event(ctx, delta)

            await self._emit("summarizer", "success", detail="回答生成完成")
            yield step_event(ctx, "summarizer", "success", detail="回答生成完成")

            final_answer = "".join(chunks)
            state["final_answer"] = final_answer
            state["llm_response"] = final_answer

            yield usage_event(
                ctx,
                TokenUsage(
                    prompt_tokens=self.usage_totals["prompt_tokens"] + collector.prompt_tokens,
                    completion_tokens=self.usage_totals["completion_tokens"] + collector.completion_tokens,
                ),
            )
            # 成本落库（§9.2）
            try:
                from app.runtime.cost.manager import record_cost

                meta = state.get("metadata") or {}
                await record_cost(
                    user_id=state.get("user_id"),
                    conversation_id=str(state.get("conversation_id") or ""),
                    trace_id=str(meta.get("trace_id") or ""),
                    agent_role="react",
                    prompt_tokens=self.usage_totals["prompt_tokens"] + collector.prompt_tokens,
                    completion_tokens=self.usage_totals["completion_tokens"] + collector.completion_tokens,
                    model_id=meta.get("model_id"),
                )
            except Exception as exc:
                logger.warning(f"[ReactLoop] 成本落库失败（已降级跳过）: {exc}")
            yield done_event(ctx, "stop")

        except Exception as exc:
            yield error_event(ctx, "AGENT_LOOP_FAILED", str(exc))
            yield done_event(ctx, "error")
