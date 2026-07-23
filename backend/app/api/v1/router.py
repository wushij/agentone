"""app/api/v1/router.py — API v1 路由聚合入口"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversation import router as conversation_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.files import router as files_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.logs import router as logs_router
from app.api.v1.models import router as models_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.settings import router as settings_router
from app.api.v1.tools import router as tools_router
from app.api.v1.users import router as users_router
from app.api.v1.ws import router as ws_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(chat_router)
v1_router.include_router(conversation_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(files_router)
v1_router.include_router(knowledge_router)
v1_router.include_router(tools_router)
v1_router.include_router(prompts_router)
v1_router.include_router(models_router)
v1_router.include_router(settings_router)
v1_router.include_router(logs_router)
v1_router.include_router(users_router)
v1_router.include_router(ws_router)