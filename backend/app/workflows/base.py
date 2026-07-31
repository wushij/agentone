"""app/workflows/base.py — 工作流基类

planned：当前 chat/rag/coding/research 四个子类的 run() 均为同构透传（直接转发
 runtime.stream_sse），尚无工作流差异化逻辑；待接入 DAG 编排后再分化。
"""

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