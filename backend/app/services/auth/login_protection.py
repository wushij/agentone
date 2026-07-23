"""backend/app/services/login_protection.py"""

from redis.asyncio import Redis

CAPTCHA_AFTER_FAILURES = 3
USER_LOCK_THRESHOLD = 5
IP_BAN_THRESHOLD = 30
USER_LOCK_TTL_SECONDS = 15 * 60
IP_BAN_TTL_SECONDS = 60 * 60


class LoginProtectionService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_allowed(self, ip: str, username: str) -> None:
        if await self._is_locked(f"login:lock:ip:{ip}"):
            raise ValueError("登录失败次数过多，请 60 分钟后再试")
        if username and await self._is_locked(f"login:lock:user:{username.lower()}"):
            raise ValueError("账号已临时锁定，请 15 分钟后再试")

    async def captcha_required(self, ip: str) -> bool:
        count = await self._read_count(f"login:fail:ip:{ip}")
        return count >= CAPTCHA_AFTER_FAILURES

    async def record_failure(self, ip: str, username: str) -> None:
        ip_fails = await self._increment(f"login:fail:ip:{ip}", IP_BAN_TTL_SECONDS)
        if ip_fails >= IP_BAN_THRESHOLD:
            await self._lock(f"login:lock:ip:{ip}", IP_BAN_TTL_SECONDS)

        if username:
            user_key = f"login:fail:user:{username.lower()}"
            user_fails = await self._increment(user_key, USER_LOCK_TTL_SECONDS)
            if user_fails >= USER_LOCK_THRESHOLD:
                await self._lock(f"login:lock:user:{username.lower()}", USER_LOCK_TTL_SECONDS)

    async def clear_on_success(self, ip: str, username: str) -> None:
        await self.redis.delete(f"login:fail:ip:{ip}")
        await self.redis.delete(f"login:lock:ip:{ip}")
        if username:
            await self.redis.delete(f"login:fail:user:{username.lower()}")
            await self.redis.delete(f"login:lock:user:{username.lower()}")

    async def _is_locked(self, key: str) -> bool:
        return (await self.redis.get(key)) == "1"

    async def _lock(self, key: str, ttl_seconds: int) -> None:
        await self.redis.set(key, "1", ex=ttl_seconds)

    async def _increment(self, key: str, ttl_seconds: int) -> int:
        value = await self.redis.incr(key)
        if value == 1:
            await self.redis.expire(key, ttl_seconds)
        return value

    async def _read_count(self, key: str) -> int:
        value = await self.redis.get(key)
        if not value:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
