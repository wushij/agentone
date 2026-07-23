"""app/memory/long_term.py — 用户级长期记忆"""

from __future__ import annotations

from typing import Any

from app.memory.base import BaseMemory


class LongTermMemory(BaseMemory):
    """跨会话保存用户偏好 / 事实（进程内；可后续落库）。"""

    def __init__(self):
        self._store: dict[str, list[dict[str, Any]]] = {}

    async def save(self, key: str, items: list[dict[str, Any]]) -> None:
        bucket = self._store.setdefault(key, [])
        for item in items:
            content = str(item.get("content") or item.get("fact") or "").strip()
            if not content:
                continue
            # 去重
            if any(str(x.get("content")) == content for x in bucket):
                continue
            bucket.append({"content": content, "metadata": dict(item.get("metadata") or {})})

    async def load(self, key: str, *, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._store.get(key, [])[-limit:])

    async def clear(self, key: str) -> None:
        self._store.pop(key, None)
