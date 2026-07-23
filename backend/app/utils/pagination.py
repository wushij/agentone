"""app/utils/pagination.py"""

from __future__ import annotations

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 10000


def clamp_page(page: int, size: int, *, max_size: int = MAX_PAGE_SIZE) -> tuple[int, int]:
    return max(1, page), max(1, min(size, max_size))


def page_result(records: list, total: int) -> dict:
    return {"total": total, "records": records}


def slice_page(items: list, page: int, size: int) -> tuple[list, int]:
    page, size = clamp_page(page, size)
    total = len(items)
    start = (page - 1) * size
    return items[start : start + size], total