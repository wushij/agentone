"""app/monitor/metrics.py — 进程内指标汇总"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

from app.monitor.cost import estimate_cost_usd
from app.monitor.token import TokenStats


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests = 0
        self.errors = 0
        self.latency_ms_total = 0
        self.latency_count = 0
        self.by_provider_calls: dict[str, int] = defaultdict(int)
        self.tokens = TokenStats()
        self.cost_usd = 0.0

    def record_request(
        self,
        *,
        provider: str = "unknown",
        latency_ms: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        error: bool = False,
    ) -> None:
        with self._lock:
            self.requests += 1
            if error:
                self.errors += 1
            if latency_ms > 0:
                self.latency_ms_total += latency_ms
                self.latency_count += 1
            self.by_provider_calls[provider or "unknown"] += 1
            self.tokens.add(provider, prompt=prompt_tokens, completion=completion_tokens)
            self.cost_usd += estimate_cost_usd(
                provider, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
            )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg = (
                int(self.latency_ms_total / self.latency_count)
                if self.latency_count
                else 0
            )
            return {
                "requests": self.requests,
                "errors": self.errors,
                "avgLatencyMs": avg,
                "providerCalls": dict(self.by_provider_calls),
                "tokens": self.tokens.snapshot(),
                "estimatedCostUsd": round(self.cost_usd, 6),
            }


_metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    return _metrics
