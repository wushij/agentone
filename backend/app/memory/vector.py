"""app/memory/vector.py — 向量记忆（轻量进程内；可后续接 RagService）"""

from __future__ import annotations

import math
from typing import Any

from app.memory.base import BaseMemory


def _tokenize(text: str) -> set[str]:
    return {t for t in text.lower().replace("\n", " ").split() if len(t) >= 2}


def _score(query: str, text: str) -> float:
    q, d = _tokenize(query), _tokenize(text)
    if not q or not d:
        return 0.0
    inter = len(q & d)
    return inter / math.sqrt(len(q) * len(d))


class VectorMemory(BaseMemory):
    """按会话保存可检索片段，默认关键词相似度（无外部向量库依赖）。"""

    def __init__(self):
        self._store: dict[str, list[dict[str, Any]]] = {}

    async def save(self, key: str, items: list[dict[str, Any]]) -> None:
        bucket = self._store.setdefault(key, [])
        for item in items:
            text = str(item.get("content") or item.get("text") or "").strip()
            if not text:
                continue
            bucket.append({"text": text, "metadata": dict(item.get("metadata") or {})})

    async def load(self, key: str, *, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._store.get(key, [])[-limit:])

    async def clear(self, key: str) -> None:
        self._store.pop(key, None)

    async def search(self, key: str, query: str, *, top_k: int = 5) -> list[dict[str, Any]]:
        rows = self._store.get(key, [])
        scored = []
        for row in rows:
            s = _score(query, row.get("text", ""))
            if s > 0:
                scored.append({**row, "score": s})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
