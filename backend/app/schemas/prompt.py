"""app/schemas/prompt.py — 提示词 Pydantic Schema"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PromptCreate(BaseModel):
    name: str
    content: str
    description: str | None = None


class PromptOut(BaseModel):
    id: int
    name: str
    content: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
