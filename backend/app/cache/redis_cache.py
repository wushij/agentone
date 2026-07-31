"""app/cache/redis_cache.py — 通用 Redis 缓存（失败自动降级内存）"""

from __future__ import annotations

import json
import time
from typing import Any

from app.utils.logger import logger


class RedisCache:
    # 修复（§4.9）：降级内存缓存容量上限，避免 Redis 长时间不可用时无界增长。
    _MEM_MAX = 2000

    def __init__(self, prefix: str = "agentone"):
        self.prefix = prefix
        self._mem: dict[str, tuple[Any, float | None]] = {}

    def _mem_set(self, full: str, value: Any, expires: float | None) -> None:
        # 超上限时先清过期项，仍超则淘汰最早插入的（FIFO 近似 LRU）。
        if len(self._mem) >= self._MEM_MAX:
            now = time.time()
            for k in [k for k, (_v, e) in self._mem.items() if e is not None and now > e]:
                self._mem.pop(k, None)
            while len(self._mem) >= self._MEM_MAX:
                self._mem.pop(next(iter(self._mem)), None)
        self._mem[full] = (value, expires)

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
            if ttl and ttl > 0:
                await redis.set(full, payload, ex=ttl)
            else:
                await redis.set(full, payload)
        except Exception as exc:
            logger.warning(f"[RedisCache] SET 失败 (key={full})，降级到内存: {exc}")
            expires = time.time() + ttl if ttl > 0 else None
            try:
                self._mem_set(full, json.loads(payload), expires)
            except Exception:
                self._mem_set(full, value, expires)

    async def incr(self, key: str) -> int:
        """修复（§4.9）：原子递增（Redis INCR），供版本号等并发安全递增；降级内存也递增。"""
        full = self._key(key)
        try:
            from app.db.redis import get_redis

            redis = await get_redis()
            return int(await redis.incr(full))
        except Exception as exc:
            logger.warning(f"[RedisCache] INCR 失败 (key={full})，降级内存: {exc}")
            cur = self._mem.get(full, (0, None))[0]
            try:
                nxt = int(cur) + 1
            except Exception:
                nxt = 1
            self._mem_set(full, nxt, None)
            return nxt

    async def delete(self, key: str) -> None:
        full = self._key(key)
        try:
            from app.db.redis import get_redis

            redis = await get_redis()
            await redis.delete(full)
        except Exception as exc:
            logger.warning(f"[RedisCache] DELETE 失败 (key={full}): {exc}")
        self._mem.pop(full, None)
