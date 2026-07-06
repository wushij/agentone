"""backend/app/schemas/auth.py"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    captcha_id: str | None = Field(None, alias="captchaId")
    captcha_answer: str | None = Field(None, alias="captchaAnswer")

    model_config = {"populate_by_name": True}


class ProfileUpdateRequest(BaseModel):
    nickname: str = Field(..., min_length=1)
    avatar: str | None = None


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword")
    new_password: str = Field(..., min_length=6, alias="newPassword")

    model_config = {"populate_by_name": True}


class AuthPayload(BaseModel):
    token: str
    token_type: str = "Bearer"
    id: int
    username: str
    nickname: str | None = None
    avatar: str | None = None
    role: str
    status: int
    permissions: list[str] = []
    full_access: bool = Field(False, alias="fullAccess")

    model_config = {"populate_by_name": True, "by_alias": True}


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    captcha_id: str | None = Field(default=None, alias="captchaId")
    captcha_answer: str | None = Field(default=None, alias="captchaAnswer")

    model_config = {"populate_by_name": True}
