"""app/monitor/cost.py — 粗略成本估算（可按价目表调整）"""

from __future__ import annotations

# USD per 1M tokens（示意价，可后续配置化）
_PRICE_PER_1M = {
    "deepseek": {"prompt": 0.14, "completion": 0.28},
    "openai": {"prompt": 0.15, "completion": 0.60},
    "mock": {"prompt": 0.0, "completion": 0.0},
}


def estimate_cost_usd(
    provider: str,
    *,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    price = _PRICE_PER_1M.get((provider or "").lower(), _PRICE_PER_1M["openai"])
    return (prompt_tokens * price["prompt"] + completion_tokens * price["completion"]) / 1_000_000
