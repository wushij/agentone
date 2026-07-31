"""app/db/redis.py"""

import asyncio

from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url

from app.config.settings import settings

_redis_lock = asyncio.Lock()

_redis: Redis | None = None


async def init_redis() -> Redis:
    global _redis
    _redis = redis_from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def get_redis() -> Redis:
    # 修复（§4.9）：惰性初始化加锁（双检），避免并发首调创建多个客户端、旧实例泄漏。
    global _redis
    if _redis is None:
        async with _redis_lock:
            if _redis is None:
                await init_redis()
    return _redis