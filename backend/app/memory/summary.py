"""app/memory/summary.py — 会话摘要记忆"""

from __future__ import annotations

import json
from typing import Any

from app.memory.base import BaseMemory


class SummaryMemory(BaseMemory):
    """每个会话保留一条滚动摘要，降低长对话 token。"""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def save(self, key: str, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        # items[-1]["content"] 视为最新摘要文本
        text = str(items[-1].get("content") or items[-1].get("summary") or "").strip()
        if text:
            self._store[key] = text

    async def load(self, key: str, *, limit: int = 20) -> list[dict[str, Any]]:
        text = self._store.get(key)
        if not text:
            return []
        return [{"role": "system", "content": text, "type": "summary"}]

    async def clear(self, key: str) -> None:
        self._store.pop(key, None)

    async def get_text(self, key: str) -> str:
        return self._store.get(key, "")

    async def set_text(self, key: str, summary: str) -> None:
        self._store[key] = summary.strip()

    def export(self) -> str:
        return json.dumps(self._store, ensure_ascii=False)
