"""app/events/bus.py — 异步事件总线 (EventBus)

§11 升级：除进程内分发外，额外镜像到 Redis Stream（消费组/ack/重放能力的基础），
实现跨进程领域事件；Redis 不可用时仅走进程内，不阻断主链路。
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from app.events.message import EventMessage

HandlerFunc = Callable[[EventMessage], Awaitable[None]]

_STREAM_KEY = "agentone:events"
_STREAM_MAXLEN = 10000


class EventBus:

    def __init__(self):
        self._listeners: dict[str, list[HandlerFunc]] = {}
        self._mirror_redis = True

    def subscribe(self, event_type: str, handler: HandlerFunc) -> None:
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: HandlerFunc) -> None:
        if event_type in self._listeners and handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)

    async def publish(self, event: EventMessage) -> None:
        event_type = str(event.event_type)
        handlers = self._listeners.get(event_type, [])
        if handlers:
            await asyncio.gather(*(h(event) for h in handlers), return_exceptions=True)
        if self._mirror_redis:
            await self._mirror_to_stream(event_type, event)

    async def _mirror_to_stream(self, event_type: str, event: EventMessage) -> None:
        try:
            from app.db.redis import get_redis

            redis = await get_redis()
            await redis.xadd(
                _STREAM_KEY,
                {
                    "event_type": event_type,
                    "sender": event.sender,
                    "data": json.dumps(event.data, ensure_ascii=False, default=str),
                    "ts": event.timestamp.isoformat(),
                },
                maxlen=_STREAM_MAXLEN,
                approximate=True,
            )
        except Exception:
            # Redis 不可用：降级仅进程内，下次自动重试
            pass


event_bus = EventBus()
