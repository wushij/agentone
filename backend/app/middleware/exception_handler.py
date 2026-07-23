"""app/middleware/exception_handler.py"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.response import fail


async def http_exception_handler(_request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(detail, code=exc.status_code),
    )


async def value_error_handler(_request: Request, exc: ValueError):
    return JSONResponse(status_code=200, content=fail(str(exc), code=400))