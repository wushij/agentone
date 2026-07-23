"""app/events/bus.py — 异步事件总线 (EventBus)"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.events.message import EventMessage

HandlerFunc = Callable[[EventMessage], Awaitable[None]]


class EventBus:

    def __init__(self):
        self._listeners: dict[str, list[HandlerFunc]] = {}

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


event_bus = EventBus()
