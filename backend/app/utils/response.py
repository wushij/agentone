"""app/utils/response.py"""

from typing import Any


def success(data: Any = None, message: str = "ok", code: int = 200) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}


def fail(message: str, code: int = 400, data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}


def success_paginated(
    records: list[Any],
    total: int,
    *,
    message: str = "ok",
    code: int = 200,
    **extra: Any,
) -> dict[str, Any]:
    data: dict[str, Any] = {"total": total, "records": records}
    data.update(extra)
    return success(data, message=message, code=code)
