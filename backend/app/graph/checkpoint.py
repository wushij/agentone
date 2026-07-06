"""backend/app/graph/checkpoint.py"""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import get_settings


def create_checkpointer() -> BaseCheckpointSaver:
    settings = get_settings()
    if settings.REDIS_URL:
        try:
            from langgraph.checkpoint.redis import RedisSaver

            return RedisSaver.from_conn_string(settings.REDIS_URL)
        except ImportError:
            pass
    return MemorySaver()
