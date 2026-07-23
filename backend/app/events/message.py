"""app/events/message.py — 全局事件消息模型"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.constants.event import EventEnum


class EventMessage(BaseModel):
    event_type: EventEnum | str
    data: dict[str, Any] = Field(default_factory=dict)
    sender: str = "system"
    timestamp: datetime = Field(default_factory=datetime.now)
