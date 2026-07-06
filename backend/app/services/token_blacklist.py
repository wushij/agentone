"""backend/app/services/token_blacklist.py"""

from fastapi import Depends
from redis.asyncio import Redis

from app.db.redis import get_redis


class TokenBlacklistService:
    def __init__(self, redis: Redis = Depends(get_redis)):
        self.redis = redis

    async def is_blacklisted(self, jti: str) -> bool:
        return bool(await self.redis.exists(f"token:blacklist:{jti}"))

    async def add(self, jti: str, ttl_seconds: int) -> None:
        await self.redis.set(f"token:blacklist:{jti}", "1", ex=ttl_seconds)
