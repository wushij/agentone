"""backend/app/api/auth.py"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.utils.response import success
from app.api.deps import bearer_scheme, get_current_user
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthPayload,
    LoginRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    RegisterRequest,
)
from app.services.auth.auth_service import AuthService
from app.services.auth.captcha_service import CaptchaService
from app.services.auth.login_protection import LoginProtectionService
from app.services.user.role_service import RoleService
from app.utils.client_ip import get_client_ip

router = APIRouter(prefix="/api/auth", tags=["认证"])


def get_auth_service(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthService:
    return AuthService(
        db=db,
        login_protection=LoginProtectionService(redis),
        captcha_service=CaptchaService(redis),
        role_service=RoleService(),
    )


@router.post("/login")
async def login(
    request: Request,
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    data = await service.login(body, get_client_ip(request))
    return success(data.model_dump(by_alias=True))


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
    redis: Redis = Depends(get_redis),
):
    token = credentials.credentials if credentials else ""
    await service.logout(token, redis)
    return success(None, message="退出成功")


@router.get("/info")
def info(
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    data = service.info(user)
    return success(data.model_dump(by_alias=True))


@router.get("/captcha")
async def captcha(service: AuthService = Depends(get_auth_service)):
    return success(await service.captcha())


@router.get("/captcha/required")
async def captcha_required(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    return success(await service.captcha_required(get_client_ip(request)))


@router.post("/register")
async def register(
    request: Request,
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    data = await service.register(body, get_client_ip(request))
    return success(data.model_dump(by_alias=True), message="注册成功")


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
    redis: Redis = Depends(get_redis),
):
    token = credentials.credentials if credentials else ""
    if not token:
        raise ValueError("未提供 Token")
    data = await service.refresh_token(token, redis)
    return success(data.model_dump(by_alias=True), message="Token 已刷新")


@router.put("/profile")
def update_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    data = service.update_profile(user, body)
    return success(data.model_dump(by_alias=True))


@router.put("/password")
def change_password(
    body: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    service.change_password(user, body)
    return success("密码修改成功")