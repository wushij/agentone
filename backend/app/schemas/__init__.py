"""app/schemas — Pydantic 数据模型基包"""

from app.schemas.auth import (
    AuthPayload,
    LoginRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    RegisterRequest,
)
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationDetail,
    ConversationItem,
    ConversationListResponse,
    ConversationUpdateRequest,
    MessageItem,
)
from app.schemas.dashboard import DashboardStatsOut
from app.schemas.file import FileAssetOut
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeQueryRequest
from app.schemas.model import ModelConfigOut
from app.schemas.prompt import PromptCreate, PromptOut
from app.schemas.settings import SystemSettingsUpdate
from app.schemas.tool import ToolConfigOut, ToolExecuteRequest
from app.schemas.user import BatchDeleteConversationsRequest, UserCreateRequest, UserItem, UserUpdateRequest

__all__ = [
    "AuthPayload",
    "LoginRequest",
    "PasswordChangeRequest",
    "ProfileUpdateRequest",
    "RegisterRequest",
    "ConversationCreateRequest",
    "ConversationUpdateRequest",
    "ConversationItem",
    "ConversationListResponse",
    "MessageItem",
    "ConversationDetail",
    "DashboardStatsOut",
    "FileAssetOut",
    "KnowledgeBaseCreate",
    "KnowledgeQueryRequest",
    "ModelConfigOut",
    "PromptCreate",
    "PromptOut",
    "SystemSettingsUpdate",
    "ToolConfigOut",
    "ToolExecuteRequest",
    "UserItem",
    "UserCreateRequest",
    "UserUpdateRequest",
    "BatchDeleteConversationsRequest",
]
