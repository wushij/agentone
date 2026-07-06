"""backend/main.py"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.dashboard import router as dashboard_router
from app.api.files import router as files_router
from app.api.knowledge import router as knowledge_router
from app.api.logs import router as logs_router
from app.api.models import router as models_router
from app.api.prompts import router as prompts_router
from app.api.settings import router as settings_router
from app.api.tools import router as tools_router
from app.api.users import router as users_router
from app.api.ws import init_notify_listener, router as ws_router, shutdown_notify_listener
from app.common.response import fail
from app.db import redis as redis_module
from app.middleware.rate_limit import RateLimitMiddleware


def _print_startup_banner() -> None:
    green, bold, reset = "\033[92m", "\033[1m", "\033[0m"
    print(
        f"\n{green}{bold}"
        "  +------------------------------+\n"
        "  |     AgentOne 后端启动成功     |\n"
        "  +------------------------------+"
        f"{reset}\n",
        flush=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import SessionLocal
    from app.db.seed import seed_all
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()

    await redis_module.init_redis()
    await init_notify_listener()
    _print_startup_banner()
    yield
    await shutdown_notify_listener()
    await redis_module.close_redis()


app = FastAPI(title="AgentOne", version="1.0.0", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(dashboard_router)
app.include_router(files_router)
app.include_router(knowledge_router)
app.include_router(tools_router)
app.include_router(prompts_router)
app.include_router(models_router)
app.include_router(settings_router)
app.include_router(logs_router)
app.include_router(users_router)
app.include_router(ws_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(detail, code=exc.status_code),
    )


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    return JSONResponse(status_code=200, content=fail(str(exc), code=400))


@app.get("/health")
async def health():
    return {"status": "ok"}
