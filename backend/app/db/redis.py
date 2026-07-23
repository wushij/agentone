"""app/db/redis.py"""

from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url

from app.config.settings import settings

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
    if _redis is None:
        await init_redis()
    return _redis