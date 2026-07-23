"""Redis lock for active SSE streams per conversation."""

from __future__ import annotations

from redis.asyncio import Redis

from app.db.redis import get_redis

_LOCK_PREFIX = "sse:active:"
_TTL_SECONDS = 300


class SseLockService:
    def __init__(self, redis: Redis):
        self.redis = redis

    def _key(self, conversation_id: str) -> str:
        return f"{_LOCK_PREFIX}{conversation_id}"

    async def acquire(self, conversation_id: str, owner: str) -> bool:
        key = self._key(conversation_id)
        acquired = await self.redis.set(key, owner, nx=True, ex=_TTL_SECONDS)
        return bool(acquired)

    async def release(self, conversation_id: str, owner: str) -> None:
        key = self._key(conversation_id)
        current = await self.redis.get(key)
        if current and (current.decode() if isinstance(current, bytes) else str(current)) == owner:
            await self.redis.delete(key)

    async def refresh(self, conversation_id: str, owner: str) -> None:
        key = self._key(conversation_id)
        current = await self.redis.get(key)
        if current and (current.decode() if isinstance(current, bytes) else str(current)) == owner:
            await self.redis.expire(key, _TTL_SECONDS)


async def get_sse_lock_service() -> SseLockService:
    redis = await get_redis()
    return SseLockService(redis)
