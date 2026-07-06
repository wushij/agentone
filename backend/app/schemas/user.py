"""backend/app/schemas/user.py"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserItem(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    avatar: str | None = None
    role: str
    status: int
    created_at: datetime | None = Field(default=None, alias="createdAt")
    last_login_at: datetime | None = Field(default=None, alias="lastLoginAt")

    model_config = {"populate_by_name": True, "by_alias": True}


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    role: str = "user"


class UserUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)
    role: str | None = None
    status: int | None = None


class BatchDeleteConversationsRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)

    model_config = {"populate_by_name": True}
