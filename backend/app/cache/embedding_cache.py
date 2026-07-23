"""app/cache/embedding_cache.py — Embedding 向量缓存"""

from __future__ import annotations

import hashlib
from typing import Any

from app.cache.redis_cache import RedisCache


class EmbeddingCache:
    def __init__(self) -> None:
        self._cache = RedisCache(prefix="agentone:emb")

    @staticmethod
    def make_key(*, model: str, text: str) -> str:
        raw = f"{model}|{text.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def get(self, key: str) -> list[float] | None:
        value = await self._cache.get(key)
        if isinstance(value, list):
            return [float(x) for x in value]
        return None

    async def set(self, key: str, vector: list[float], *, ttl: int = 86400) -> None:
        await self._cache.set(key, vector, ttl=ttl)
