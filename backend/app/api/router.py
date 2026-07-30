"""app/api/router.py — 总路由入口（/api/v1 规范路径 + /api 向下兼容）"""

from fastapi import APIRouter

from app.api.v1.router import v1_router

api_router = APIRouter(prefix="/api")

# 规范路径：/api/v1/xxx (如 /api/v1/auth/login)
api_router.include_router(v1_router, prefix="/v1")

# 兼容路径：/api/xxx (如 /api/auth/login，保障旧接口向下兼容)
api_router.include_router(v1_router)