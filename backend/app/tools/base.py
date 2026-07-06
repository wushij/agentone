"""backend/app/tools/base.py"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    output: str
    duration_ms: int
    error: str = ""


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError
