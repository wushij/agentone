"""backend/app/api/chat.py"""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.conversation_service import ConversationService
from app.services.graph_runner import GraphRunner
from app.services.sse_lock import get_sse_lock_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatStreamRequest(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    message: str
    model_id: str | None = Field(default=None, alias="modelId")
    kb_id: str | None = Field(default=None, alias="kbId")
    enable_tools: bool = Field(default=True, alias="enableTools")

    model_config = {"populate_by_name": True}


class ChatRegenerateRequest(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    model_id: str | None = Field(default=None, alias="modelId")
    kb_id: str | None = Field(default=None, alias="kbId")
    enable_tools: bool = Field(default=True, alias="enableTools")

    model_config = {"populate_by_name": True}


def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


@router.post("/stream")
async def chat_stream(
    body: ChatStreamRequest,
    request: Request,
    user: User = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
    db: Session = Depends(get_db),
):
    lock_owner = f"{user.id}:{uuid.uuid4().hex[:8]}"
    sse_lock = await get_sse_lock_service()

    if not await sse_lock.acquire(body.conversation_id, lock_owner):
        async def busy_stream():
            err = {
                "conversationId": body.conversation_id,
                "messageId": str(uuid.uuid4()),
                "code": "CONVERSATION_BUSY",
                "message": "该会话已有进行中的流式对话，请稍后再试",
            }
            done = {"conversationId": body.conversation_id, "finishReason": "error"}
            yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps(done, ensure_ascii=False)}\n\n"

        return StreamingResponse(busy_stream(), media_type="text/event-stream")

    history = conv_service.build_langchain_history(user.id, body.conversation_id)
    conv_service.add_message(user.id, body.conversation_id, "user", body.message)
    AuditLogService(db).write(
        user_id=user.id,
        module="chat",
        action="stream_start",
        detail=f"conversation={body.conversation_id}",
    )

    runner = GraphRunner()
    assistant_parts: list[str] = []
    usage_tokens = 0
    assistant_message_id: str | None = None

    async def event_generator():
        nonlocal usage_tokens, assistant_message_id
        tools_executed = []
        try:
            async for event in runner.stream_sse(
                body.message,
                session_id=body.conversation_id,
                user_id=str(user.id),
                conversation_id=body.conversation_id,
                history=history,
                enable_tools=body.enable_tools,
                model_id=body.model_id,
                kb_id=body.kb_id,
            ):
                if await request.is_disconnected():
                    break

                if event.event == "token":
                    assistant_parts.append(event.data.get("delta", ""))
                elif event.event == "usage":
                    usage_tokens = int(event.data.get("totalTokens", 0))
                elif event.event == "done":
                    assistant_message_id = event.data.get("messageId")
                elif event.event == "tool_start":
                    tools_executed.append({
                        "id": f"{event.data.get('tool')}_{len(tools_executed)}",
                        "tool": event.data.get("tool"),
                        "input": event.data.get("input"),
                        "status": "running"
                    })
                elif event.event == "tool_end":
                    tool_name = event.data.get("tool")
                    for t in reversed(tools_executed):
                        if t["tool"] == tool_name and t["status"] == "running":
                            t["status"] = "error" if event.data.get("error") else "done"
                            t["output"] = event.data.get("output")
                            t["durationMs"] = event.data.get("durationMs")
                            break

                yield event.encode()
                await sse_lock.refresh(body.conversation_id, lock_owner)

            answer = "".join(assistant_parts).strip()
            if answer or tools_executed:
                conv_service.add_message(
                    user.id,
                    body.conversation_id,
                    "assistant",
                    answer,
                    message_id=assistant_message_id,
                    tokens=usage_tokens,
                    tools=tools_executed if tools_executed else None,
                )
                AuditLogService(db).write(
                    user_id=user.id,
                    module="chat",
                    action="stream_done",
                    detail=f"conversation={body.conversation_id} tokens={usage_tokens}",
                )
        finally:
            await sse_lock.release(body.conversation_id, lock_owner)


    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/regenerate")
async def chat_regenerate(
    body: ChatRegenerateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
    db: Session = Depends(get_db),
):
    history = conv_service.build_langchain_history(user.id, body.conversation_id)
    if not history:
        raise HTTPException(status_code=400, detail="会话历史为空，无法重新生成")

    detail = conv_service.get_conversation(user.id, body.conversation_id)
    if detail.messages and detail.messages[-1].role == "assistant":
        conv_service.delete_last_message(user.id, body.conversation_id)
        history = conv_service.build_langchain_history(user.id, body.conversation_id)
        detail = conv_service.get_conversation(user.id, body.conversation_id)

    if not detail.messages:
        raise HTTPException(status_code=400, detail="会话历史为空，无法重新生成")

    last_user_msg = None
    for msg in reversed(detail.messages):
        if msg.role == "user":
            last_user_msg = msg
            break

    if not last_user_msg:
        raise HTTPException(status_code=400, detail="找不到上一次用户输入")

    user_message_content = last_user_msg.content

    lock_owner = f"{user.id}:{uuid.uuid4().hex[:8]}"
    sse_lock = await get_sse_lock_service()

    if not await sse_lock.acquire(body.conversation_id, lock_owner):
        async def busy_stream():
            err = {
                "conversationId": body.conversation_id,
                "messageId": str(uuid.uuid4()),
                "code": "CONVERSATION_BUSY",
                "message": "该会话已有进行中的流式对话，请稍后再试",
            }
            done = {"conversationId": body.conversation_id, "finishReason": "error"}
            yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps(done, ensure_ascii=False)}\n\n"

        return StreamingResponse(busy_stream(), media_type="text/event-stream")

    AuditLogService(db).write(
        user_id=user.id,
        module="chat",
        action="regenerate_start",
        detail=f"conversation={body.conversation_id}",
    )

    runner = GraphRunner()
    assistant_parts: list[str] = []
    usage_tokens = 0
    assistant_message_id: str | None = None

    async def event_generator():
        nonlocal usage_tokens, assistant_message_id
        tools_executed = []
        try:
            async for event in runner.stream_sse(
                user_message_content,
                session_id=body.conversation_id,
                user_id=str(user.id),
                conversation_id=body.conversation_id,
                history=history,
                enable_tools=body.enable_tools,
                model_id=body.model_id,
                kb_id=body.kb_id,
            ):
                if await request.is_disconnected():
                    break

                if event.event == "token":
                    assistant_parts.append(event.data.get("delta", ""))
                elif event.event == "usage":
                    usage_tokens = int(event.data.get("totalTokens", 0))
                elif event.event == "done":
                    assistant_message_id = event.data.get("messageId")
                elif event.event == "tool_start":
                    tools_executed.append({
                        "id": f"{event.data.get('tool')}_{len(tools_executed)}",
                        "tool": event.data.get("tool"),
                        "input": event.data.get("input"),
                        "status": "running"
                    })
                elif event.event == "tool_end":
                    tool_name = event.data.get("tool")
                    for t in reversed(tools_executed):
                        if t["tool"] == tool_name and t["status"] == "running":
                            t["status"] = "error" if event.data.get("error") else "done"
                            t["output"] = event.data.get("output")
                            t["durationMs"] = event.data.get("durationMs")
                            break

                yield event.encode()
                await sse_lock.refresh(body.conversation_id, lock_owner)

            answer = "".join(assistant_parts).strip()
            if answer or tools_executed:
                conv_service.add_message(
                    user.id,
                    body.conversation_id,
                    "assistant",
                    answer,
                    message_id=assistant_message_id,
                    tokens=usage_tokens,
                    tools=tools_executed if tools_executed else None,
                )
                AuditLogService(db).write(
                    user_id=user.id,
                    module="chat",
                    action="regenerate_done",
                    detail=f"conversation={body.conversation_id} tokens={usage_tokens}",
                )
        finally:
            await sse_lock.release(body.conversation_id, lock_owner)


    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )