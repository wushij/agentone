"""app/workflows/coding.py — 编程工作流"""

from collections.abc import AsyncIterator
from typing import Any

from app.core.events.events import SseEvent
from app.workflows.base import BaseWorkflow


class CodingWorkflow(BaseWorkflow):
    name = "coding"
    description = "编程辅助工作流"

    async def run(self, user_input: str, **kwargs: Any) -> AsyncIterator[SseEvent]:
        from app.core.engine.engine import get_engine
        engine = get_engine()
        async for event in engine.stream_sse(user_input, **kwargs):
            yield event