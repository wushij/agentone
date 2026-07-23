"""app/middleware/rate_limit.py"""

from __future__ import annotations

import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.system.settings_store import settings_store
from app.utils.client_ip import get_client_ip
from app.utils.response import fail

_SKIP_PATHS = {"/health", "/api/auth/captcha", "/api/auth/captcha/required", "/api/settings/public"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/") or path in _SKIP_PATHS:
            return await call_next(request)

        settings = settings_store.get_all()
        client_ip = get_client_ip(request)

        blacklist = settings.get("ipBlacklist", "")
        if blacklist:
            blocked_ips = [ip.strip() for ip in blacklist.replace("\n", ",").split(",") if ip.strip()]
            if client_ip in blocked_ips:
                return JSONResponse(
                    status_code=403,
                    content=fail("您的 IP 已被系统封禁", code=403),
                )

        if not settings.get("rateLimitEnabled", True):
            return await call_next(request)

        limit = int(settings.get("rateLimitPerMinute", 120))
        key = f"rate:{client_ip}:{int(time.time()) // 60}"

        try:
            from app.db.redis import get_redis

            redis = await get_redis()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 65)
            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content=fail("请求过于频繁，请稍后再试", code=429),
                )
        except Exception as exc:
            from app.utils.logger import logger

            logger.warning(f"[RateLimitMiddleware] Redis 限流检查失败，放行请求: {exc}")

        return await call_next(request)