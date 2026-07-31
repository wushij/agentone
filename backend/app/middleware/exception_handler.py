"""app/middleware/exception_handler.py"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.logger import logger
from app.utils.response import fail


async def http_exception_handler(_request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(detail, code=exc.status_code),
    )


async def value_error_handler(_request: Request, exc: ValueError):
    # 修复（§4.9）：业务 ValueError 返回 HTTP 400（而非 200），使 HTTP 层监控/客户端能正确判错；
    # 响应体仍携业务 code=400 与消息，前端契约不变。
    return JSONResponse(status_code=400, content=fail(str(exc), code=400))


async def global_exception_handler(_request: Request, exc: Exception):
    # 兑底（§4.9）：未捕获异常统一转 500 + 日志，避免碎栈泄露与监控失明。
    logger.error(f"[UnhandledException] {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content=fail("服务器内部错误，请稍后重试", code=500))