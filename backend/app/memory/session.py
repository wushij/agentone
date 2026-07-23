"""app/memory/session.py — 当前会话短期记忆（进程内 + 可同步 DB 历史）"""

from __future__ import annotations

from typing import Any

from app.memory.base import BaseMemory


class SessionMemory(BaseMemory):
    """保存最近若干轮对话，供 Agent 快速取上下文。"""

    def __init__(self, max_messages: int = 40):
        self._store: dict[str, list[dict[str, Any]]] = {}
        self.max_messages = max_messages

    async def save(self, key: str, items: list[dict[str, Any]]) -> None:
        bucket = self._store.setdefault(key, [])
        bucket.extend(items)
        if len(bucket) > self.max_messages:
            self._store[key] = bucket[-self.max_messages :]

    async def load(self, key: str, *, limit: int = 20) -> list[dict[str, Any]]:
        messages = self._store.get(key, [])
        return messages[-limit:]

    async def clear(self, key: str) -> None:
        self._store.pop(key, None)

    async def replace(self, key: str, items: list[dict[str, Any]]) -> None:
        self._store[key] = list(items)[-self.max_messages :]
