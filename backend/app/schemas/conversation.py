"""backend/app/schemas/conversation.py"""

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)


class ConversationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    is_archived: bool | None = Field(default=None, alias="isArchived")


class ConversationItem(BaseModel):
    id: str
    title: str
    is_archived: bool = Field(False, alias="isArchived")
    message_count: int = Field(0, alias="messageCount")
    total_tokens: int = Field(0, alias="totalTokens")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True, "by_alias": True}


class ConversationListResponse(BaseModel):
    records: list[ConversationItem]
    total: int

    model_config = {"populate_by_name": True, "by_alias": True}


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: str = Field(alias="createdAt")
    tokens: int = 0
    tools: list | None = None

    model_config = {"populate_by_name": True, "by_alias": True}


class ConversationDetail(ConversationItem):
    messages: list[MessageItem] = Field(default_factory=list)

    model_config = {"populate_by_name": True, "by_alias": True}
