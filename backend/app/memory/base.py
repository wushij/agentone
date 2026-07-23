"""app/memory/base.py — Memory 抽象"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseMemory(ABC):
    """统一记忆接口：按 key（通常是 conversation_id / user_id）读写。"""

    @abstractmethod
    async def save(self, key: str, items: list[dict[str, Any]]) -> None: ...

    @abstractmethod
    async def load(self, key: str, *, limit: int = 20) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def clear(self, key: str) -> None: ...
