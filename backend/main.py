"""backend/main.py"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.v1.ws import init_notify_listener, shutdown_notify_listener
from app.db import redis as redis_module
from app.middleware.exception_handler import http_exception_handler, value_error_handler
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_log import RequestLogMiddleware
from app.utils.logger import logger
from app.utils.response import fail


def _print_startup_banner() -> None:
    from app.knowledge.stores.qdrant import get_qdrant_store
    qdrant = get_qdrant_store()
    q_str = f"Qdrant 向量库 ({qdrant.url})" if qdrant else "JSON 向量存储 (保底)"

    green, cyan, bold, reset = "\033[92m", "\033[96m", "\033[1m", "\033[0m"
    print(
        f"\n{green}{bold}"
        "  +------------------------------------+\n"
        "  |       AgentOne 后端启动成功        |\n"
        "  +------------------------------------+\n"
        f"  {cyan}► 向量引擎: {q_str}{reset}\n",
        flush=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 安全（§17.4）：SECRET_KEY 弱值强校验——默认弱值下大声告警；
    # 设 REQUIRE_STRONG_SECRET=true 时拒绝启动（生产强制）。
    try:
        from app.config.settings import get_settings

        _s = get_settings()
        if _s.SECRET_KEY == "change-me-in-production":
            msg = "[Security] SECRET_KEY 仍为默认弱值，生产环境必须在 .env 中修改！"
            if getattr(_s, "REQUIRE_STRONG_SECRET", False):
                raise RuntimeError(msg + " (REQUIRE_STRONG_SECRET=true 已拒绝启动)")
            logger.warning(msg)
    except RuntimeError:
        raise
    except Exception:
        pass

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
    except Exception as e:
        logger.error(f"Failed to initialize storage directories: {e}")
    await init_notify_listener()
    try:
        from app.events.subscribers import register_subscribers

        register_subscribers()
    except Exception as e:
        logger.error(f"Failed to register event subscribers: {e}")
    try:
        from app.runtime import get_runtime

        await get_runtime().setup()
    except Exception as e:
        logger.error(f"Failed to initialize Agent Runtime: {e}")
    try:
        from app.events.stream_consumer import start_stream_consumer
        from app.memory.scheduler import start_memory_decay
        from app.knowledge.stores.qdrant import get_qdrant_store

        start_memory_decay()
        start_stream_consumer()
        get_qdrant_store()
    except Exception as e:
        logger.error(f"Failed to start background workers: {e}")
    try:
        from app.runtime.scheduler import get_scheduler
        from app.services.task.handlers import run_agent_task

        scheduler = get_scheduler()
        scheduler.register_handler("agent", run_agent_task)
        scheduler.register_handler("report", run_agent_task)
        scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start task scheduler: {e}")
    _print_startup_banner()
    yield
    try:
        from app.events.stream_consumer import stop_stream_consumer
        from app.memory.scheduler import stop_memory_decay
        from app.runtime.scheduler import get_scheduler

        await stop_memory_decay()
        await stop_stream_consumer()
        await get_scheduler().stop()
    except Exception:
        pass
    await shutdown_notify_listener()
    await redis_module.close_redis()


app = FastAPI(title="AgentOne", version="1.0.0", lifespan=lifespan)

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
]

app.add_middleware(RequestLogMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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