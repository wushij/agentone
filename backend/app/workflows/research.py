"""app/workflows/research.py — 研究调研工作流"""

from collections.abc import AsyncIterator
from typing import Any

from app.core.events.events import SseEvent
from app.workflows.base import BaseWorkflow


class ResearchWorkflow(BaseWorkflow):
    name = "research"
    description = "研究调研工作流"

    async def run(self, user_input: str, **kwargs: Any) -> AsyncIterator[SseEvent]:
        from app.runtime import get_runtime
        async for event in get_runtime().stream_sse(user_input, **kwargs):
            yield event