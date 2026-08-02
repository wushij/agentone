"""app/runtime/monitor/otel.py — 全链路 Trace 与深度可观测性模块"""

from __future__ import annotations

import contextvars
import logging
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_CURRENT_TRACE_ID: contextvars.ContextVar[str] = contextvars.ContextVar("current_trace_id", default="")
_CURRENT_SPAN_ID: contextvars.ContextVar[str] = contextvars.ContextVar("current_span_id", default="")


def get_current_trace_id() -> str:
    tid = _CURRENT_TRACE_ID.get()
    if not tid:
        tid = str(uuid.uuid4())
        _CURRENT_TRACE_ID.set(tid)
    return tid


def set_current_trace_id(trace_id: str) -> None:
    if trace_id:
        _CURRENT_TRACE_ID.set(trace_id)


class SpanContext:
    def __init__(self, name: str, attributes: dict[str, Any] | None = None):
        self.name = name
        self.attributes = attributes or {}
        self.span_id = str(uuid.uuid4())
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.previous_span_id = _CURRENT_SPAN_ID.get()
        _CURRENT_SPAN_ID.set(self.span_id)
        trace_id = get_current_trace_id()
        logger.debug(f"[Trace:{trace_id}][Span:{self.span_id}] START {self.name} - {self.attributes}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.perf_counter() - self.start_time) * 1000)
        trace_id = get_current_trace_id()
        status = "error" if exc_type else "success"
        logger.debug(
            f"[Trace:{trace_id}][Span:{self.span_id}] END {self.name} "
            f"status={status} duration={duration_ms}ms"
        )
        _CURRENT_SPAN_ID.set(self.previous_span_id)


def trace_span(name: str, attributes: dict[str, Any] | None = None) -> SpanContext:
    return SpanContext(name, attributes)
