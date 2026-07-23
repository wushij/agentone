"""app/cache/redis_cache.py — 通用 Redis 缓存（失败自动降级内存）"""

from __future__ import annotations

import json
import time
from typing import Any

from app.utils.logger import logger


class RedisCache:
    def __init__(self, prefix: str = "agentone"):
        self.prefix = prefix
        self._mem: dict[str, tuple[Any, float | None]] = {}

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        full = self._key(key)
        try:
            from app.db.redis import get_redis

            redis = await get_redis()
            raw = await redis.get(full)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning(f"[RedisCache] GET 失败 (key={full})，降级到内存: {exc}")
            item = self._mem.get(full)
            if not item:
                return None
            value, expires = item
            if expires is not None and time.time() > expires:
                self._mem.pop(full, None)
                return None
            return value

    async def set(self, key: str, value: Any, *, ttl: int = 3600) -> None:
        full = self._key(key)
        payload = json.dumps(value, ensure_ascii=False)
        try:
            from app.db.redis import get_redis

            redis = await get_redis()
            await redis.set(full, payload, ex=ttl)
        except Exception as exc:
            logger.warning(f"[RedisCache] SET 失败 (key={full})，降级到内存: {exc}")
            expires = time.time() + ttl if ttl > 0 else None
            try:
                self._mem[full] = (json.loads(payload), expires)
            except Exception:
                self._mem[full] = (value, expires)

    async def delete(self, key: str) -> None:
        full = self._key(key)
        try:
            from app.db.redis import get_redis

            redis = await get_redis()
            await redis.delete(full)
        except Exception as exc:
            logger.warning(f"[RedisCache] DELETE 失败 (key={full}): {exc}")
        self._mem.pop(full, None)
