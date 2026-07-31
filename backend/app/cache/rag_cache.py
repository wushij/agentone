"""app/cache/rag_cache.py — RAG 检索结果缓存（§8.3 L1）

版本化主动失效：每个 kb 维护一个 version 计数，缓存 key 内嵌所有涉及库的版本；
文档增删改时 bump_version(kb_id) 使旧 key 自然失效（无需扫描删除）。
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.cache.redis_cache import RedisCache


class RagCache:
    def __init__(self) -> None:
        self._cache = RedisCache(prefix="agentone:rag")
        self._ver = RedisCache(prefix="agentone:ragver")

    async def _versions(self, kb_ids: list[str]) -> str:
        parts: list[str] = []
        for kid in sorted(str(x) for x in kb_ids):
            v = await self._ver.get(kid)
            parts.append(f"{kid}:{v or 0}")
        return "|".join(parts)

    async def make_key(self, *, kb_ids: list[str], query: str) -> str:
        versions = await self._versions(kb_ids)
        # ranker 版本前缀：排序算法与阈值过滤变更时自动失效旧缓存（当前 v3=2-gram 词组分词 + 精准得分阈值）
        raw = f"rank:v3|{versions}|{query.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def get(self, key: str) -> list[dict[str, Any]] | None:
        value = await self._cache.get(key)
        if isinstance(value, list):
            return value
        return None

    async def set(self, key: str, chunks: list[dict[str, Any]], *, ttl: int = 600) -> None:
        await self._cache.set(key, chunks, ttl=ttl)

    async def bump_version(self, kb_id: str) -> None:
        """文档增删改时调用：使该库相关的 L1 缓存 key 全部失效。
        修复（§4.9）：用原子 INCR 递增版本号，避免“读-加一-写”并发丢递增。"""
        await self._ver.incr(kb_id)
