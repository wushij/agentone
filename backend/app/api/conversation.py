"""backend/app/api/conversation.py"""

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.common.response import success
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.conversation import ConversationCreateRequest, ConversationUpdateRequest
from app.schemas.user import BatchDeleteConversationsRequest
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["会话"])


def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


from fastapi import APIRouter, Depends, Query

@router.get("")
def list_conversations(
    q: str = Query(default=""),
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    data = service.list_conversations(user.id, keyword=q)
    return success(data.model_dump(by_alias=True))


@router.post("")
def create_conversation(
    body: ConversationCreateRequest,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    data = service.create_conversation(user.id, body)
    return success(data.model_dump(by_alias=True))


@router.post("/batch-delete")
def batch_delete_conversations(
    body: BatchDeleteConversationsRequest,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    deleted = service.batch_delete_conversations(user.id, body.ids)
    return success({"deleted": deleted}, message=f"已删除 {deleted} 个会话")


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    data = service.get_conversation(user.id, conversation_id)
    return success(data.model_dump(by_alias=True))


@router.get("/{conversation_id}/workflow-snapshot")
def get_workflow_snapshot(
    conversation_id: str,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    data = service.get_workflow_snapshot(user.id, conversation_id)
    return success(data)


@router.put("/{conversation_id}")
def update_conversation(
    conversation_id: str,
    body: ConversationUpdateRequest,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    data = service.update_conversation(user.id, conversation_id, body)
    return success(data.model_dump(by_alias=True))


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    service.delete_conversation(user.id, conversation_id)
    return success(None, message="删除成功")


@router.delete("/{conversation_id}/messages/{message_id}")
def delete_message(
    conversation_id: str,
    message_id: str,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    service.delete_message(user.id, conversation_id, message_id)
    return success(None, message="消息已删除")


@router.get("/{conversation_id}/export")
def export_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    content = service.export_markdown(user.id, conversation_id)
    return PlainTextResponse(
        content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{conversation_id}.md"'},
    )


from pydantic import BaseModel

class BatchDeleteRequest(BaseModel):
    ids: list[str]

@router.post("/batch-delete")
def batch_delete(
    body: BatchDeleteRequest,
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    service.batch_delete_conversations(user.id, body.ids)
    return success(None, message="批量删除成功")
