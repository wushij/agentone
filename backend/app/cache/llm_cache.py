"""app/cache/llm_cache.py — LLM 响应缓存"""

from __future__ import annotations

import hashlib
from typing import Any

from app.cache.redis_cache import RedisCache


class LlmCache:
    def __init__(self) -> None:
        self._cache = RedisCache(prefix="agentone:llm")

    @staticmethod
    def make_key(*, model: str, prompt: str, temperature: float = 0.7) -> str:
        raw = f"{model}|{temperature}|{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def get(self, key: str) -> str | None:
        value = await self._cache.get(key)
        return str(value) if value is not None else None

    async def set(self, key: str, content: str, *, ttl: int = 1800) -> None:
        await self._cache.set(key, content, ttl=ttl)
