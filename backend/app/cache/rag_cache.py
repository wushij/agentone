"""app/cache/rag_cache.py — RAG 检索结果缓存"""

from __future__ import annotations

import hashlib
from typing import Any

from app.cache.redis_cache import RedisCache


class RagCache:
    def __init__(self) -> None:
        self._cache = RedisCache(prefix="agentone:rag")

    @staticmethod
    def make_key(*, kb_ids: list[str], query: str) -> str:
        ids = ",".join(sorted(str(x) for x in kb_ids))
        raw = f"{ids}|{query.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def get(self, key: str) -> list[dict[str, Any]] | None:
        value = await self._cache.get(key)
        if isinstance(value, list):
            return value
        return None

    async def set(self, key: str, chunks: list[dict[str, Any]], *, ttl: int = 600) -> None:
        await self._cache.set(key, chunks, ttl=ttl)
