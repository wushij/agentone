"""app/api/router.py — 总路由入口（包含 /v1 隔离及向下兼容）"""

from fastapi import APIRouter

from app.api.v1.router import v1_router

api_router = APIRouter()

# 挂载 /v1 版本号子路由 (如 /api/v1/auth/login)
api_router.include_router(v1_router, prefix="/v1")

# 挂载基础路由 (如 /api/auth/login，保障全套旧接口向下兼容)
api_router.include_router(v1_router, prefix="")