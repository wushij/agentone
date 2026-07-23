"""app/constants/event.py — 全局事件枚举"""

from enum import Enum


class EventEnum(str, Enum):
    CHAT_START = "chat_start"
    CHAT_CHUNK = "chat_chunk"
    CHAT_END = "chat_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SYSTEM_NOTIFY = "system_notify"
