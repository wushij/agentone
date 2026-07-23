"""app/core/engine.py — Agent 执行引擎"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from app.agents.planner import detect_intent, planner_node
from app.agents.reviewer import reviewer_node
from app.agents.writer import stream_summarizer_tokens
from app.core.events.events import (
    AgentStatusEvent,
    NODE_LABELS,
    SseEvent,
    StreamContext,
    TokenUsage,
    done_event,
    error_event,
    step_event,
    token_event,
    tool_end_event,
    tool_start_event,
    usage_event,
)
from app.core.context.state import AgentState, init_state
from app.tools.registry import get_tool, is_tool_enabled

AgentStatusCallback = Callable[[AgentStatusEvent], Awaitable[None] | None]


def create_checkpointer():
    from langgraph.checkpoint.memory import MemorySaver

    try:
        from app.config.settings import get_settings
        settings = get_settings()
        if settings.REDIS_URL:
            try:
                from langgraph.checkpoint.redis import RedisSaver
                return RedisSaver.from_conn_string(settings.REDIS_URL)
            except ImportError:
                pass
    except Exception:
        pass
    return MemorySaver()


async def _intent_node(state: AgentState) -> dict:
    user_input = state.get("user_input") or ""
    intent, tool_name, tool_input = detect_intent(user_input)

    if (state.get("metadata") or {}).get("enable_tools") is False and intent != "prompt_engineer":
        return {
            "intent": "chat",
            "tool_name": "",
            "tool_input": {},
            "current_node": "researcher",
            "metadata": {"detected_intent": "chat", "tools_disabled": True},
        }

    return {
        "intent": intent,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "current_node": "researcher",
        "metadata": {"detected_intent": intent},
    }


async def _tool_node(state: AgentState) -> dict:
    tool_name = state.get("tool_name") or ""
    tool_input = state.get("tool_input") or {}
    retries = state.get("tool_retries") or 0

    tool = get_tool(tool_name)
    if tool is None:
        return {
            "tool_error": f"工具未注册: {tool_name}",
            "error": f"工具未注册: {tool_name}",
            "current_node": "tool",
        }
    if not is_tool_enabled(tool_name):
        return {
            "tool_error": f"工具已禁用: {tool_name}",
            "error": f"工具已禁用: {tool_name}",
            "current_node": "tool",
        }

    result = await tool.run(
        **tool_input,
        _user_id=state.get("user_id"),
        _conversation_id=state.get("conversation_id"),
    )
    if result.error:
        try:
            from app.config.settings import get_settings

            max_retries = get_settings().TOOL_MAX_RETRIES
        except Exception:
            max_retries = 3
        if retries < max_retries:
            return {
                "tool_error": result.error,
                "tool_retries": retries + 1,
                "current_node": "tool",
                "metadata": {"tool_retry": retries + 1},
            }
        _write_tool_log(
            state,
            tool_name=tool_name,
            params=tool_input,
            result=result.error,
            duration_ms=result.duration_ms,
            status="error",
        )
        return {
            "tool_error": result.error,
            "error": result.error,
            "current_node": "tool",
            "metadata": {"tool_duration_ms": result.duration_ms},
        }

    _write_tool_log(
        state,
        tool_name=tool_name,
        params=tool_input,
        result=result.output,
        duration_ms=result.duration_ms,
        status="success",
    )
    return {
        "tool_result": result.output,
        "tool_error": "",
        "current_node": "tool",
        "metadata": {"tool_duration_ms": result.duration_ms},
    }


def _write_tool_log(state: AgentState, *, tool_name: str, params: dict, result: str, duration_ms: int, status: str) -> None:
    import json
    user_id = state.get("user_id")
    if not user_id:
        return
    from app.db.session import SessionLocal
    from app.models.tool_log import ToolLog
    db = SessionLocal()
    try:
        db.add(
            ToolLog(
                user_id=int(user_id),
                conversation_id=state.get("conversation_id"),
                tool_name=tool_name,
                params=json.dumps(params, ensure_ascii=False),
                result=result[:4000] if result else None,
                duration_ms=duration_ms,
                status=status,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


async def _unsupported_node(state: AgentState) -> dict:
    intent = state.get("intent") or "unknown"
    return {
        "final_answer": (
            f"识别到意图「{intent}」，但当前没有匹配的内置工具。"
            "已支持：普通对话、calculator（计算器）、search（网络搜索）、"
            "file（用户文件读取）、database（只读数据库查询）。"
        ),
        "llm_response": "",
        "error": "",
        "current_node": "unsupported",
    }


async def _error_handler_node(state: AgentState) -> dict:
    message = state.get("error") or state.get("tool_error") or "执行失败，请稍后重试"
    return {
        "final_answer": message,
        "error": message,
        "current_node": "error_handler",
    }


def _route_after_researcher(state: AgentState) -> str:
    if state.get("error"):
        return "reviewer"
    intent = state.get("intent") or "chat"
    if intent in ("chat", "prompt_engineer"):
        return "reviewer"
    tool_name = state.get("tool_name") or ""
    if get_tool(tool_name) is not None:
        return "tool"
    return "unsupported"


def _route_after_tool(state: AgentState) -> str:
    if state.get("error"):
        return "error_handler"
    if state.get("tool_error") and not state.get("tool_result"):
        retries = state.get("tool_retries") or 0
        if retries < 3:
            return "tool"
        return "error_handler"
    return "reviewer"


_compiled_graph = None


def _build_graph():
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("researcher", _intent_node)
    graph.add_node("tool", _tool_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("unsupported", _unsupported_node)
    graph.add_node("error_handler", _error_handler_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")

    graph.add_conditional_edges(
        "researcher",
        _route_after_researcher,
        {
            "reviewer": "reviewer",
            "tool": "tool",
            "unsupported": "unsupported",
        },
    )

    graph.add_conditional_edges(
        "tool",
        _route_after_tool,
        {
            "reviewer": "reviewer",
            "tool": "tool",
            "error_handler": "error_handler",
        },
    )

    graph.add_edge("reviewer", END)
    graph.add_edge("unsupported", END)
    graph.add_edge("error_handler", END)

    _compiled_graph = graph.compile(checkpointer=create_checkpointer())
    return _compiled_graph


def _merge_state(state: AgentState, update: dict[str, Any]) -> AgentState:
    merged: AgentState = dict(state)
    for key, value in update.items():
        if key == "messages" and value:
            merged["messages"] = list(merged.get("messages") or []) + list(value)
        elif key == "metadata" and value:
            merged["metadata"] = {**(merged.get("metadata") or {}), **value}
        else:
            merged[key] = value
    return merged


def _thread_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id or str(uuid.uuid4())}}


def _step_detail(node_name: str, state: AgentState) -> tuple[str, str]:
    meta = state.get("metadata") or {}
    if node_name == "planner":
        plan = str(meta.get("plan") or "").strip()
        if plan:
            return (plan, "")
        return ("完成意图分析", "")
    if node_name == "researcher":
        intent = state.get("intent") or meta.get("detected_intent") or "chat"
        labels = {
            "chat": "普通对话",
            "calculator": "计算器",
            "search": "搜索",
            "file": "文件",
            "database": "数据库",
            "prompt_engineer": "AI 编程提示词工程",
        }
        parts: list[str] = []
        if meta.get("rag_context"):
            parts.append("知识库上下文已注入")
        parts.append(f"识别意图：{labels.get(intent, intent)}")
        return ("；".join(parts), "")
    if node_name == "tool":
        name = state.get("tool_name") or ""
        result = str(state.get("tool_result") or "").strip()
        if result:
            return (result, name)
        return (name or "工具执行", name)
    if node_name == "reviewer":
        review = str(meta.get("review") or "").strip()
        if review:
            return (review, "")
        return ("审阅通过", "")
    if node_name == "summarizer":
        return ("流式生成最终回答", "")
    return ("", "")


async def _stream_text_as_tokens(ctx: StreamContext, text: str, *, chunk_size: int = 12, pause_s: float = 0.022) -> AsyncIterator[SseEvent]:
    for i in range(0, len(text), chunk_size):
        delta = text[i : i + chunk_size]
        yield token_event(ctx, delta)
        await asyncio.sleep(pause_s)


class GraphRunner:
    def __init__(self, on_agent_status: AgentStatusCallback | None = None):
        self.graph = _build_graph()
        self.on_agent_status = on_agent_status

    async def _emit_status(self, ctx: StreamContext, node: str, status: str, *, tool: str = "", elapsed_ms: int = 0, error: str = "", detail: str = "", label: str = "") -> None:
        event = AgentStatusEvent(
            conversation_id=ctx.conversation_id,
            node=node,
            status=status,  # type: ignore[arg-type]
            tool=tool,
            elapsed_ms=elapsed_ms,
            error=error,
            detail=detail,
            label=label or NODE_LABELS.get(node, node),
        )
        if self.on_agent_status:
            result = self.on_agent_status(event)
            if result is not None:
                await result

        if ctx.user_id and status in {"success", "error"}:
            try:
                from app.db.session import SessionLocal
                from app.services.system.audit_log_service import AuditLogService
                db = SessionLocal()
                try:
                    AuditLogService(db).write(
                        user_id=int(ctx.user_id),
                        module="agent",
                        action=f"{node}:{status}",
                        detail=tool or node,
                        status="success" if status == "success" else "error",
                    )
                finally:
                    db.close()
            except Exception:
                pass

        if ctx.user_id:
            try:
                from app.services.system.notify_hub import get_notify_hub
                hub = await get_notify_hub()
                await hub.publish(
                    int(ctx.user_id),
                    {
                        "type": "agent_status",
                        "payload": {
                            "conversationId": ctx.conversation_id,
                            "node": node,
                            "status": status,
                            "tool": tool,
                            "elapsedMs": elapsed_ms,
                            "error": error,
                            "detail": detail,
                            "label": event.label,
                        },
                    },
                )
            except Exception:
                pass

    async def invoke(self, user_input: str, *, session_id: str = "", user_id: str = "", conversation_id: str = "") -> AgentState:
        state = init_state(
            user_input=user_input,
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=str(uuid.uuid4()),
        )
        config = _thread_config(session_id)
        result = await self.graph.ainvoke(state, config=config)

        chunks: list[str] = []
        async for delta in stream_summarizer_tokens(result):
            chunks.append(delta)
        answer = "".join(chunks)
        result = _merge_state(
            result,
            {
                "final_answer": answer,
                "llm_response": answer,
                "messages": [AIMessage(content=answer)],
                "current_node": "summarizer",
            },
        )
        return result

    async def stream_sse(
        self,
        user_input: str,
        *,
        session_id: str = "",
        user_id: str = "",
        conversation_id: str = "",
        message_id: str | None = None,
        history: list | None = None,
        enable_tools: bool = True,
        model_id: str | None = None,
        kb_ids: list[str] | None = None,
        kb_mode: str = "generate",
    ) -> AsyncIterator[SseEvent]:
        msg_id = message_id or str(uuid.uuid4())
        conv_id = conversation_id or session_id or str(uuid.uuid4())
        thread_id = session_id or conv_id
        ctx = StreamContext(conversation_id=conv_id, message_id=msg_id, user_id=user_id)
        original_query = user_input
        resolved_kb_ids = [str(x).strip() for x in (kb_ids or []) if str(x).strip()]

        metadata: dict[str, Any] = {"enable_tools": enable_tools}
        if model_id:
            metadata["model_id"] = model_id
        if resolved_kb_ids:
            metadata["kb_ids"] = resolved_kb_ids

        yield step_event(ctx, "prepare", "running")
        yield step_event(ctx, "prepare", "success")

        if resolved_kb_ids and kb_mode == "retrieve":
            try:
                from app.services.rag.rag_service import RagService, format_kb_retrieve_answer
                yield step_event(ctx, "rag", "running")
                await self._emit_status(ctx, "rag", "running")
                rag_started = time.perf_counter()
                kb_chunks = await RagService.fetch_kb_chunks_multi(resolved_kb_ids, original_query)
                rag_ms = int((time.perf_counter() - rag_started) * 1000)
                if kb_chunks:
                    retrieve_limit = 5 if len(resolved_kb_ids) > 1 else 1
                    kb_chunks = kb_chunks[:retrieve_limit]
                    hit = len(kb_chunks)
                    kb_detail = (
                        f"知识库检索命中 {hit} 条（{len(resolved_kb_ids)} 个库）"
                        if len(resolved_kb_ids) > 1
                        else f"知识库检索命中 {hit} 条"
                    )
                    yield step_event(ctx, "rag", "success", elapsed_ms=rag_ms, detail=kb_detail)
                    await self._emit_status(ctx, "rag", "success", elapsed_ms=rag_ms, detail=f"命中 {hit} 条")
                    answer = format_kb_retrieve_answer(original_query, kb_chunks)
                    yield step_event(ctx, "format", "running")
                    completion_tokens = 0
                    async for event in _stream_text_as_tokens(ctx, answer):
                        completion_tokens += max(1, len(event.data.get("delta", "")) // 4)
                        yield event
                    yield step_event(ctx, "format", "success")
                    yield usage_event(ctx, TokenUsage(prompt_tokens=0, completion_tokens=completion_tokens))
                    yield done_event(ctx, "stop")
                    return
                yield step_event(ctx, "rag", "success", elapsed_ms=rag_ms, detail="检索无命中，改由大模型作答")
                await self._emit_status(ctx, "rag", "success", elapsed_ms=rag_ms, detail="检索无命中，改由大模型作答")
                metadata["rag_empty"] = True
            except Exception as exc:
                yield step_event(ctx, "rag", "error", error=str(exc))
                yield error_event(ctx, "RAG_FAILED", str(exc))
                yield done_event(ctx, "error")
                return

        if resolved_kb_ids:
            try:
                from app.services.rag.rag_service import RagService
                yield step_event(ctx, "rag", "running")
                rag_started = time.perf_counter()
                kb_chunks = await RagService.fetch_kb_chunks_multi(resolved_kb_ids, original_query)
                rag_ms = int((time.perf_counter() - rag_started) * 1000)
                if kb_chunks:
                    ref_text = "\n\n".join(
                        [
                            f"【资料 {idx} · {c.get('kbName', '知识库')}】\n{c['text']}"
                            for idx, c in enumerate(kb_chunks, 1)
                        ]
                    )
                    metadata["rag_context"] = ref_text
                    user_input = original_query
                kb_detail = (
                    f"知识库检索命中 {len(kb_chunks or [])} 条（{len(resolved_kb_ids)} 个库）"
                    if len(resolved_kb_ids) > 1
                    else (
                        f"知识库检索命中 {len(kb_chunks or [])} 条"
                        if kb_chunks
                        else "检索无命中，改由大模型作答"
                    )
                )
                yield step_event(ctx, "rag", "success", elapsed_ms=rag_ms, detail=kb_detail)
            except Exception:
                yield step_event(ctx, "rag", "error", error="知识库检索失败，将直接作答")

        state = init_state(
            user_input=user_input,
            session_id=thread_id,
            user_id=user_id,
            conversation_id=conv_id,
            message_id=msg_id,
            history=history,
        )
        state["metadata"] = {**(state.get("metadata") or {}), **metadata}
        config = _thread_config(thread_id)

        try:
            yield step_event(ctx, "planner", "running")
            node_started: dict[str, float] = {"planner": time.perf_counter()}

            async for update in self.graph.astream(state, config=config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    state = _merge_state(state, node_output)
                    elapsed = 0
                    if node_name in node_started:
                        elapsed = int((time.perf_counter() - node_started[node_name]) * 1000)
                    detail, tool_name = _step_detail(node_name, state)
                    yield step_event(ctx, node_name, "success", elapsed_ms=elapsed, detail=detail, tool=tool_name)
                    await self._emit_status(ctx, node_name, "success", elapsed_ms=elapsed, detail=detail, tool=tool_name)

                    if node_name == "tool":
                        tool_name = state.get("tool_name") or "tool"
                        tool_input = state.get("tool_input") or {}
                        await self._emit_status(ctx, "tool", "running", tool=tool_name)
                        yield tool_start_event(ctx, tool_name, tool_input)

                        duration = int((state.get("metadata") or {}).get("tool_duration_ms", 0))
                        if state.get("tool_error") and not state.get("tool_result"):
                            yield tool_end_event(ctx, tool_name, "", duration, error=state.get("tool_error") or "")
                            await self._emit_status(ctx, "tool", "error", tool=tool_name, error=state.get("tool_error") or "")
                        else:
                            yield tool_end_event(ctx, tool_name, state.get("tool_result") or "", duration)
                            await self._emit_status(ctx, "tool", "success", tool=tool_name)

                    if node_name == "planner":
                        node_started["researcher"] = time.perf_counter()
                        yield step_event(ctx, "researcher", "running")
                    elif node_name == "researcher":
                        route = _route_after_researcher(state)
                        if route == "tool":
                            node_started["tool"] = time.perf_counter()
                            yield step_event(ctx, "tool", "running")
                        elif route == "reviewer":
                            node_started["reviewer"] = time.perf_counter()
                            yield step_event(ctx, "reviewer", "running")
                    elif node_name == "tool":
                        route = _route_after_tool(state)
                        if route == "tool":
                            node_started["tool"] = time.perf_counter()
                            yield step_event(ctx, "tool", "running")
                        elif route == "reviewer":
                            node_started["reviewer"] = time.perf_counter()
                            yield step_event(ctx, "reviewer", "running")

            if state.get("error") and not state.get("final_answer"):
                yield error_event(ctx, "TOOL_FAILED", state["error"])
                yield done_event(ctx, "error")
                return

            yield step_event(ctx, "summarizer", "running")
            await self._emit_status(ctx, "summarizer", "running")
            completion_tokens = 0
            chunks = []
            async for delta in stream_summarizer_tokens(state):
                completion_tokens += max(1, len(delta) // 4)
                chunks.append(delta)
                yield token_event(ctx, delta)
            await self._emit_status(ctx, "summarizer", "success", detail="回答生成完成")
            yield step_event(ctx, "summarizer", "success", detail="回答生成完成")

            final_answer = "".join(chunks)
            state["final_answer"] = final_answer
            state["llm_response"] = final_answer

            yield usage_event(ctx, TokenUsage(prompt_tokens=80, completion_tokens=completion_tokens))
            yield done_event(ctx, "stop")

        except Exception as exc:
            yield error_event(ctx, "LLM_TIMEOUT", str(exc))
            yield done_event(ctx, "error")

    async def stream_sse_encoded(self, user_input: str, **kwargs: Any) -> AsyncIterator[str]:
        async for event in self.stream_sse(user_input, **kwargs):
            yield event.encode()


_engine: GraphRunner | None = None


def get_engine() -> GraphRunner:
    global _engine
    if _engine is None:
        _engine = GraphRunner()
    return _engine