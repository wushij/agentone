"""backend/app/services/auth_service.py"""

from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.security import create_access_token, safe_decode_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthPayload, LoginRequest, PasswordChangeRequest, ProfileUpdateRequest, RegisterRequest
from app.services.auth.captcha_service import CaptchaService
from app.services.auth.login_protection import LoginProtectionService
from app.services.user.role_service import RoleService
from app.services.auth.token_blacklist import TokenBlacklistService
from app.services.user.user_service import UserService
from app.services.auth.token_blacklist import TokenBlacklistService


class AuthService:
    def __init__(
        self,
        db: Session,
        login_protection: LoginProtectionService,
        captcha_service: CaptchaService,
        role_service: RoleService,
    ):
        self.db = db
        self.users = UserRepository(db)
        self.login_protection = login_protection
        self.captcha_service = captcha_service
        self.role_service = role_service

    async def login(self, request: LoginRequest, client_ip: str) -> AuthPayload:
        username = request.username.strip()
        await self.login_protection.check_allowed(client_ip, username)

        if await self.login_protection.captcha_required(client_ip):
            await self.captcha_service.verify(request.captcha_id, request.captcha_answer)

        user = self.users.get_by_username(username)
        if user is None or not verify_password(request.password, user.password):
            await self.login_protection.record_failure(client_ip, username)
            raise ValueError("用户名或密码错误")
        if user.status != 1:
            raise ValueError("账号已被禁用")

        await self.login_protection.clear_on_success(client_ip, username)
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        from app.services.system.audit_log_service import AuditLogService

        AuditLogService(self.db).write(
            user_id=user.id,
            module="auth",
            action="login",
            detail=f"ip={client_ip}",
        )
        return self._build_auth_payload(user)

    async def logout(self, token: str, redis: Redis) -> None:
        payload = safe_decode_access_token(token)
        if not payload:
            return
        user_id = payload.get("sub")
        if user_id:
            from app.services.system.audit_log_service import AuditLogService

            AuditLogService(self.db).write(
                user_id=int(user_id),
                module="auth",
                action="logout",
            )
        jti = payload.get("jti")
        if not jti:
            return
        exp = payload.get("exp")
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        if exp:
            ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 60)
        await TokenBlacklistService(redis).add(jti, ttl)

    def info(self, user: User) -> AuthPayload:
        return self._build_auth_payload(user)

    async def captcha(self) -> dict[str, str]:
        return await self.captcha_service.create()

    async def captcha_required(self, client_ip: str) -> dict[str, bool]:
        return {"required": await self.login_protection.captcha_required(client_ip)}

    def update_profile(self, user: User, request: ProfileUpdateRequest) -> AuthPayload:
        user.nickname = request.nickname
        user.avatar = request.avatar
        self.db.commit()
        self.db.refresh(user)
        return self._build_auth_payload(user)

    def change_password(self, user: User, request: PasswordChangeRequest) -> None:
        from app.core.security import hash_password

        if not verify_password(request.old_password, user.password):
            raise ValueError("原密码不正确")
        user.password = hash_password(request.new_password)
        self.db.commit()

    async def register(self, request: RegisterRequest, client_ip: str) -> AuthPayload:
        if await self.login_protection.captcha_required(client_ip):
            await self.captcha_service.verify(request.captcha_id, request.captcha_answer)
        user_item = UserService(self.db).register(
            request.username,
            request.password,
            request.nickname,
        )
        user = self.users.get_by_id(user_item.id)
        if user is None:
            raise ValueError("注册失败")
        from app.services.system.audit_log_service import AuditLogService

        AuditLogService(self.db).write(
            user_id=user.id,
            module="auth",
            action="register",
            detail=f"ip={client_ip}",
        )
        return self._build_auth_payload(user)

    async def refresh_token(self, token: str, redis: Redis) -> AuthPayload:
        payload = safe_decode_access_token(token)
        if not payload:
            raise ValueError("Token 无效或已过期")
        jti = payload.get("jti")
        if jti and await TokenBlacklistService(redis).is_blacklisted(jti):
            raise ValueError("Token 已失效")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token 无效")
        user = self.users.get_by_id(int(user_id))
        if user is None or user.status != 1:
            raise ValueError("用户不存在或已被禁用")
        if jti:
            exp = payload.get("exp")
            ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            if exp:
                ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 60)
            await TokenBlacklistService(redis).add(jti, ttl)
        return self._build_auth_payload(user)

    def _build_auth_payload(self, user: User) -> AuthPayload:
        permissions = self.role_service.get_permissions(user.role)
        return AuthPayload(
            token=create_access_token(user.id, user.role),
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar=user.avatar,
            role=user.role,
            status=user.status,
            permissions=permissions,
            fullAccess=self.role_service.has_full_access(user.role),
        )
