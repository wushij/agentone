"""app/monitor/trace.py — 简易耗时追踪"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Span:
    name: str
    started_at: float
    ended_at: float = 0.0
    meta: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        end = self.ended_at or time.perf_counter()
        return int((end - self.started_at) * 1000)


class Tracer:
    def __init__(self) -> None:
        self.spans: list[Span] = []

    @contextmanager
    def span(self, name: str, **meta) -> Iterator[Span]:
        item = Span(name=name, started_at=time.perf_counter(), meta=dict(meta))
        try:
            yield item
        finally:
            item.ended_at = time.perf_counter()
            self.spans.append(item)

    def snapshot(self) -> list[dict]:
        return [
            {"name": s.name, "durationMs": s.duration_ms, "meta": s.meta}
            for s in self.spans
        ]
