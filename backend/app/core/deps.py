"""backend/app/core/deps.py"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.security import safe_decode_access_token
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.role_service import RoleService
from app.services.token_blacklist import TokenBlacklistService

bearer_scheme = HTTPBearer(auto_error=False)

_ADMIN_ROLES = frozenset({"admin", "super_admin"})


async def _resolve_user_from_payload(
    payload: dict | None,
    db: Session,
    blacklist: TokenBlacklistService,
) -> User:
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")

    jti = payload.get("jti")
    if jti and await blacklist.is_blacklisted(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")

    user = UserRepository(db).get_by_id(int(user_id))
    if user is None or user.status != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已被禁用")
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    blacklist: TokenBlacklistService = Depends(),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或 Token 无效")

    payload = safe_decode_access_token(credentials.credentials)
    return await _resolve_user_from_payload(payload, db, blacklist)


async def resolve_user_from_token(token: str, db: Session, redis: Redis) -> User:
    blacklist = TokenBlacklistService(redis)
    payload = safe_decode_access_token(token)
    return await _resolve_user_from_payload(payload, db, blacklist)


async def get_current_user_from_token(
    token: str,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    return await resolve_user_from_token(token, db, redis)


def require_permission(permission: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        perms = RoleService().get_permissions(user.role)
        if "*" in perms or permission in perms:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    return checker


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role in _ADMIN_ROLES or RoleService().has_full_access(user.role):
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
