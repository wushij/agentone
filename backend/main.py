"""backend/main.py"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.ws import init_notify_listener, shutdown_notify_listener
from app.db import redis as redis_module
from app.middleware.exception_handler import http_exception_handler, value_error_handler
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_log import RequestLogMiddleware
from app.utils.response import fail


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
    try:
        from app.storage import ensure_storage_dirs

        ensure_storage_dirs()
    except Exception:
        pass
    await init_notify_listener()
    _print_startup_banner()
    yield
    await shutdown_notify_listener()
    await redis_module.close_redis()


app = FastAPI(title="AgentOne", version="1.0.0", lifespan=lifespan)

app.add_middleware(RequestLogMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)


@app.get("/health")
async def health():
    return {"status": "ok"}