"""backend/app/services/graph_runner.py — Graph 执行与 SSE 流式编排"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from langchain_core.messages import AIMessage

from app.graph.builder import get_compiled_graph
from app.graph.events import (
    AgentStatusEvent,
    SseEvent,
    StreamContext,
    TokenUsage,
    done_event,
    error_event,
    token_event,
    tool_end_event,
    tool_start_event,
    usage_event,
)
from app.graph.nodes.summarizer_node import stream_summarizer_tokens
from app.graph.router import route_after_researcher
from app.graph.state import AgentState, init_state

AgentStatusCallback = Callable[[AgentStatusEvent], Awaitable[None] | None]


def _merge_state(state: AgentState, update: dict[str, Any]) -> AgentState:
    merged: AgentState = dict(state)
    for key, value in update.items():
        if key == "messages" and value:
            merged["messages"] = list(merged.get("messages") or []) + list(value)
        elif key == "metadata" and value:
            merged["metadata"] = {**(merged.get("metadata") or {}), **value}
        else:
            merged[key] = value  # type: ignore[literal-required]
    return merged


def _thread_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id or str(uuid.uuid4())}}


class GraphRunner:
    def __init__(self, on_agent_status: AgentStatusCallback | None = None):
        self.graph = get_compiled_graph()
        self.on_agent_status = on_agent_status

    async def _emit_status(
        self,
        ctx: StreamContext,
        node: str,
        status: str,
        *,
        tool: str = "",
        elapsed_ms: int = 0,
        error: str = "",
    ) -> None:
        event = AgentStatusEvent(
            conversation_id=ctx.conversation_id,
            node=node,
            status=status,  # type: ignore[arg-type]
            tool=tool,
            elapsed_ms=elapsed_ms,
            error=error,
        )
        if self.on_agent_status:
            result = self.on_agent_status(event)
            if result is not None:
                await result

        if ctx.user_id and status in {"success", "error"}:
            try:
                from app.db.session import SessionLocal
                from app.services.audit_log_service import AuditLogService

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
                from app.services.notify_hub import get_notify_hub

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
                        },
                    },
                )
            except Exception:
                pass

    async def invoke(
        self,
        user_input: str,
        *,
        session_id: str = "",
        user_id: str = "",
        conversation_id: str = "",
    ) -> AgentState:
        state = init_state(
            user_input=user_input,
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=str(uuid.uuid4()),
        )
        config = _thread_config(session_id)
        result = await self.graph.ainvoke(state, config=config)

        # 调取 Summarizer Agent 汇总最终输出
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
        kb_id: str | None = None,
    ) -> AsyncIterator[SseEvent]:
        msg_id = message_id or str(uuid.uuid4())
        conv_id = conversation_id or session_id or str(uuid.uuid4())
        thread_id = session_id or conv_id
        ctx = StreamContext(conversation_id=conv_id, message_id=msg_id, user_id=user_id)

        metadata: dict[str, Any] = {"enable_tools": enable_tools}
        if model_id:
            metadata["model_id"] = model_id

        # RAG Knowledge Base Retrieval & Injection
        if kb_id:
            try:
                from app.db.session import SessionLocal
                from app.services.model_service import ModelService
                from app.services.rag_service import RagService
                from app.api.knowledge import _load_kb

                db = SessionLocal()
                try:
                    kb_list = _load_kb()
                    kb_cfg = next((k for k in kb_list if k["id"] == kb_id), None)
                    if kb_cfg:
                        top_k = int(kb_cfg.get("topK", 3))
                        score_threshold = float(kb_cfg.get("scoreThreshold", 0.5))

                        model_service = ModelService(db)
                        default_model = model_service.get_default()
                        api_key = default_model.api_key if default_model else None
                        base_url = default_model.base_url if default_model else None
                        model_name = default_model.model_name if default_model else "text-embedding-3-small"

                        chunks = await RagService.query_kb(
                            kb_id=kb_id,
                            query=user_input,
                            top_k=top_k,
                            score_threshold=score_threshold,
                            api_key=api_key,
                            base_url=base_url,
                            model=model_name
                        )
                        if chunks:
                            ref_text = "\n".join([f"{idx+1}. {c['text']}" for idx, c in enumerate(chunks)])
                            metadata["rag_context"] = ref_text
                            user_input = (
                                "【知识库参考资料】：\n"
                                f"{ref_text}\n"
                                "-----------------\n"
                                "请结合上述参考资料回答用户问题。如果参考资料中没有相关信息，请按您默认的通用常识回答，并告知用户在参考资料中未检索到内容。\n\n"
                                f"用户问题：{user_input}"
                            )
                finally:
                    db.close()
            except Exception:
                pass

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
            # 顺序执行多代理工作流各节点 (planner -> researcher -> tool -> reviewer)
            async for update in self.graph.astream(state, config=config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    state = _merge_state(state, node_output)
                    await self._emit_status(ctx, node_name, "running")

                    if node_name == "tool":
                        tool_name = state.get("tool_name") or "tool"
                        tool_input = state.get("tool_input") or {}
                        await self._emit_status(ctx, "tool", "running", tool=tool_name)
                        yield tool_start_event(ctx, tool_name, tool_input)

                        duration = int((state.get("metadata") or {}).get("tool_duration_ms", 0))
                        if state.get("tool_error") and not state.get("tool_result"):
                            yield tool_end_event(
                                ctx,
                                tool_name,
                                "",
                                duration,
                                error=state.get("tool_error") or "",
                            )
                            await self._emit_status(
                                ctx,
                                "tool",
                                "error",
                                tool=tool_name,
                                error=state.get("tool_error") or "",
                            )
                        else:
                            yield tool_end_event(
                                ctx,
                                tool_name,
                                state.get("tool_result") or "",
                                duration,
                            )
                            await self._emit_status(ctx, "tool", "success", tool=tool_name)

                    await self._emit_status(ctx, node_name, "success")

            if state.get("error") and not state.get("final_answer"):
                yield error_event(ctx, "TOOL_FAILED", state["error"])
                yield done_event(ctx, "error")
                return

            # 调用 Summarizer Agent 汇总最终输出并流式生成 tokens
            await self._emit_status(ctx, "summarizer", "running")
            completion_tokens = 0
            chunks = []
            async for delta in stream_summarizer_tokens(state):
                completion_tokens += max(1, len(delta) // 4)
                chunks.append(delta)
                yield token_event(ctx, delta)
            await self._emit_status(ctx, "summarizer", "success")

            final_answer = "".join(chunks)
            state["final_answer"] = final_answer
            state["llm_response"] = final_answer

            yield usage_event(ctx, TokenUsage(prompt_tokens=80, completion_tokens=completion_tokens))
            yield done_event(ctx, "stop")

        except Exception as exc:  # noqa: BLE001
            yield error_event(ctx, "LLM_TIMEOUT", str(exc))
            yield done_event(ctx, "error")

    async def stream_sse_encoded(self, user_input: str, **kwargs: Any) -> AsyncIterator[str]:
        async for event in self.stream_sse(user_input, **kwargs):
            yield event.encode()
