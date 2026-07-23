"""app/workflows/base.py — 工作流基类"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from app.core.events.events import SseEvent


class BaseWorkflow(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def run(self, user_input: str, **kwargs: Any) -> AsyncIterator[SseEvent]:
        ...