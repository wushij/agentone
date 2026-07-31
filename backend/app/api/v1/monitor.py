"""backend/app/api/v1/monitor.py — 成本中心（§9.2）+ Prometheus /metrics（§13.2）"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.deps import get_current_user, require_admin
from app.models.user import User
from app.monitor.metrics import get_metrics
from app.runtime.cost import get_cost_manager
from app.utils.response import success

router = APIRouter(tags=["监控与成本"])


@router.get("/cost/summary")
def cost_summary(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(require_admin),
):
    """成本中心：按天/模型/Agent 聚合出账。"""
    return success(get_cost_manager().aggregate(days=days))


@router.get("/cost/me")
def my_cost(user: User = Depends(get_current_user)):
    """当前用户今日成本与限额。"""
    allowed, spent, limit = get_cost_manager().check_daily_limit(user.id)
    return success({"todayUsd": round(spent, 6), "dailyLimitUsd": limit, "allowed": allowed})


def _prometheus_text(snapshot: dict) -> str:
    lines: list[str] = []
    lines.append(f"agentone_requests_total {snapshot.get('requests', 0)}")
    lines.append(f"agentone_errors_total {snapshot.get('errors', 0)}")
    lines.append(f"agentone_avg_latency_ms {snapshot.get('avgLatencyMs', 0)}")
    lines.append(f"agentone_estimated_cost_usd {snapshot.get('estimatedCostUsd', 0)}")
    tokens = snapshot.get("tokens", {})
    total = tokens.get("total", {}) if isinstance(tokens, dict) else {}
    if isinstance(total, dict):
        lines.append(f"agentone_prompt_tokens_total {total.get('promptTokens', 0)}")
        lines.append(f"agentone_completion_tokens_total {total.get('completionTokens', 0)}")
    for name, stat in (snapshot.get("cache") or {}).items():
        lines.append(f'agentone_cache_hit_rate{{name="{name}"}} {stat.get("hitRate", 0)}')
    for provider, calls in (snapshot.get("providerCalls") or {}).items():
        lines.append(f'agentone_provider_calls{{provider="{provider}"}} {calls}')
    return "\n".join(lines) + "\n"


@router.get("/metrics")
def prometheus_metrics():
    """Prometheus 文本端点（§13.2）——替代仅进程内的 MetricsRegistry 快照。"""
    return Response(content=_prometheus_text(get_metrics().snapshot()), media_type="text/plain")
