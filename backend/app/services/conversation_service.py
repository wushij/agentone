"""backend/app/services/conversation_service.py"""

from datetime import datetime, timezone

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.datetime_utils import serialize_datetime
from app.models.conversation import Conversation, new_conversation_id
from app.models.message import Message, new_message_id
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationDetail,
    ConversationItem,
    ConversationListResponse,
    ConversationUpdateRequest,
    MessageItem,
)


def _effective_tokens(message: Message) -> int:
    stored = message.tokens or 0
    if stored > 0:
        return stored
    if message.role == "assistant" and message.content:
        return max(1, len(message.content) // 4)
    return 0


def _message_item(message: Message) -> MessageItem:
    return MessageItem(
        id=message.id,
        role=message.role,
        content=message.content,
        createdAt=serialize_datetime(message.created_at) or "",
        tokens=_effective_tokens(message),
        tools=message.tools,
    )


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def list_conversations(self, user_id: int, keyword: str = "") -> ConversationListResponse:
        message_count = func.count(Message.id).label("message_count")
        if keyword:
            matching_conv_ids_stmt = (
                select(Conversation.id)
                .outerjoin(Message, Message.conversation_id == Conversation.id)
                .where(
                    Conversation.user_id == user_id,
                    (Conversation.title.like(f"%{keyword}%") | Message.content.like(f"%{keyword}%"))
                )
                .group_by(Conversation.id)
            )
            matching_ids = self.db.execute(matching_conv_ids_stmt).scalars().all()
            
            stmt = (
                select(Conversation, message_count)
                .outerjoin(Message, Message.conversation_id == Conversation.id)
                .where(Conversation.id.in_(matching_ids) if matching_ids else False)
                .group_by(Conversation.id)
                .order_by(Conversation.updated_at.desc())
            )
        else:
            stmt = (
                select(Conversation, message_count)
                .outerjoin(Message, Message.conversation_id == Conversation.id)
                .where(Conversation.user_id == user_id)
                .group_by(Conversation.id)
                .order_by(Conversation.updated_at.desc())
            )
        rows = self.db.execute(stmt).all()
        items = [
            ConversationItem(
                id=conv.id,
                title=conv.title,
                isArchived=bool(conv.is_archived),
                messageCount=count or 0,
                createdAt=conv.created_at,
                updatedAt=conv.updated_at,
            )
            for conv, count in rows
        ]
        return ConversationListResponse(items=items, total=len(items))

    def create_conversation(self, user_id: int, request: ConversationCreateRequest) -> ConversationItem:
        conversation = Conversation(
            id=new_conversation_id(),
            user_id=user_id,
            title=request.title or "新对话",
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return ConversationItem(
            id=conversation.id,
            title=conversation.title,
            messageCount=0,
            createdAt=conversation.created_at,
            updatedAt=conversation.updated_at,
        )

    def get_conversation(self, user_id: int, conversation_id: str) -> ConversationDetail:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        message_items = [_message_item(m) for m in messages]
        total_tokens = sum(item.tokens for item in message_items)
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            isArchived=bool(conversation.is_archived),
            messageCount=len(messages),
            totalTokens=total_tokens,
            createdAt=conversation.created_at,
            updatedAt=conversation.updated_at,
            messages=message_items,
        )

    def get_workflow_snapshot(self, user_id: int, conversation_id: str) -> dict:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")

        rows = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id, Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .all()
        )

        latest = rows[0] if rows else None
        nodes = [
            {"node": "planner", "status": "pending"},
            {"node": "researcher", "status": "pending"},
            {"node": "tool", "status": "pending"},
            {"node": "reviewer", "status": "pending"},
            {"node": "summarizer", "status": "pending"},
        ]
        if latest is None:
            return {"conversationId": conversation_id, "updatedAt": None, "nodes": nodes}

        nodes[0]["status"] = "success"
        nodes[1]["status"] = "success"
        nodes[3]["status"] = "success"
        nodes[4]["status"] = "success"

        tools = latest.tools or []
        if tools:
            tool_elapsed = 0
            tool_names: list[str] = []
            tool_error = False
            error_text = ""
            for item in tools:
                if not isinstance(item, dict):
                    continue
                if isinstance(item.get("durationMs"), int):
                    tool_elapsed += int(item["durationMs"])
                if item.get("tool"):
                    tool_names.append(str(item["tool"]))
                if item.get("status") == "error":
                    tool_error = True
                    if not error_text and item.get("output"):
                        error_text = str(item["output"])

            nodes[2]["status"] = "error" if tool_error else "success"
            if tool_elapsed:
                nodes[2]["elapsedMs"] = tool_elapsed
            if tool_names:
                nodes[2]["tool"] = " / ".join(tool_names[:2]) + ("..." if len(tool_names) > 2 else "")
            if error_text:
                nodes[2]["error"] = error_text[:160]
        else:
            nodes[2]["status"] = "success"

        return {
            "conversationId": conversation_id,
            "updatedAt": serialize_datetime(latest.created_at),
            "nodes": nodes,
        }

    def build_langchain_history(
        self,
        user_id: int,
        conversation_id: str,
        *,
        exclude_last_user: bool = True,
    ) -> list[BaseMessage]:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")

        rows = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        if exclude_last_user and rows and rows[-1].role == "user":
            rows = rows[:-1]

        history: list[BaseMessage] = []
        for row in rows:
            if row.role == "user":
                history.append(HumanMessage(content=row.content))
            elif row.role == "assistant":
                history.append(AIMessage(content=row.content))
        return history

    def add_message(
        self,
        user_id: int,
        conversation_id: str,
        role: str,
        content: str,
        *,
        message_id: str | None = None,
        tokens: int = 0,
        tools: list | None = None,
    ) -> MessageItem:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")
        message = Message(
            id=message_id or new_message_id(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens=tokens,
            created_at=datetime.now(timezone.utc),
            tools=tools,
        )
        self.db.add(message)
        conversation.updated_at = datetime.now(timezone.utc)
        if conversation.title == "新对话" and role == "user":
            conversation.title = content[:24] + ("…" if len(content) > 24 else "")
        self.db.commit()
        self.db.refresh(message)
        return _message_item(message)

    def update_conversation(
        self, user_id: int, conversation_id: str, request: ConversationUpdateRequest
    ) -> ConversationItem:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")
        if request.title:
            conversation.title = request.title
        if request.is_archived is not None:
            conversation.is_archived = 1 if request.is_archived else 0
        self.db.commit()
        self.db.refresh(conversation)
        count = (
            self.db.query(Message).filter(Message.conversation_id == conversation_id).count()
        )
        return ConversationItem(
            id=conversation.id,
            title=conversation.title,
            isArchived=bool(conversation.is_archived),
            messageCount=count,
            createdAt=conversation.created_at,
            updatedAt=conversation.updated_at,
        )

    def delete_conversation(self, user_id: int, conversation_id: str) -> None:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")
        self.db.delete(conversation)
        self.db.commit()

    def delete_conversations_batch(self, user_id: int, conversation_ids: list[str]) -> None:
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.id.in_(conversation_ids)
        )
        rows = self.db.execute(stmt).scalars().all()
        for row in rows:
            self.db.delete(row)
        self.db.commit()

    def batch_delete_conversations(self, user_id: int, conversation_ids: list[str]) -> int:
        deleted = 0
        for cid in conversation_ids:
            conversation = self.db.get(Conversation, cid)
            if conversation is None or conversation.user_id != user_id:
                continue
            self.db.delete(conversation)
            deleted += 1
        self.db.commit()
        return deleted

    def delete_message(self, user_id: int, conversation_id: str, message_id: str) -> None:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")
        message = self.db.get(Message, message_id)
        if message is None or message.conversation_id != conversation_id:
            raise ValueError("消息不存在")
        self.db.delete(message)
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def truncate_from_message(self, user_id: int, conversation_id: str, message_id: str) -> str:
        """删除指定消息及其之后的所有消息，返回被删 assistant 前一条 user 消息内容。"""
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")

        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        target_idx = next((i for i, m in enumerate(messages) if m.id == message_id), -1)
        if target_idx < 0:
            raise ValueError("消息不存在")

        target = messages[target_idx]
        if target.role != "assistant":
            raise ValueError("仅支持对助手消息重新生成")

        user_content = ""
        for i in range(target_idx - 1, -1, -1):
            if messages[i].role == "user":
                user_content = messages[i].content
                break
        if not user_content:
            raise ValueError("未找到对应的用户消息")

        for m in messages[target_idx:]:
            self.db.delete(m)
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return user_content

    def export_markdown(self, user_id: int, conversation_id: str) -> str:
        detail = self.get_conversation(user_id, conversation_id)
        lines = [f"# {detail.title}", "", f"> 导出时间：{datetime.now(timezone.utc).isoformat()}", ""]
        for msg in detail.messages:
            role_label = "用户" if msg.role == "user" else "助手"
            lines.append(f"## {role_label}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
        return "\n".join(lines)

    def delete_last_message(self, user_id: int, conversation_id: str) -> None:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ValueError("会话不存在")
        last_msg = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .first()
        )
        if last_msg:
            self.db.delete(last_msg)
            self.db.commit()
