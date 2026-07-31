"""app/runtime/cost/manager.py — Cost Manager（§9.2）

从"Token 统计"到"成本治理"：
- 多维计量：每次 LLM/Embedding 调用记一条 cost_records
- 多维聚合：按用户/天/模型/Agent 角色出账
- 限额检查：用户日限额（超限返回 False，供调用方拒绝或降级）
- 价格表：优先 settings_store 的 modelPricing（DB 配置化），回退 monitor.cost 硬编码
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.utils.logger import logger


def _price_per_1m(provider: str) -> dict[str, float]:
    """价格表（USD/1M tokens）：settings_store.modelPricing 优先，回退硬编码。"""
    try:
        from app.services.system.settings_store import settings_store

        pricing = settings_store.get("modelPricing", {}) or {}
        if provider in pricing:
            p = pricing[provider]
            return {"prompt": float(p.get("prompt", 0)), "completion": float(p.get("completion", 0))}
    except Exception:
        pass
    from app.monitor.cost import _PRICE_PER_1M

    return _PRICE_PER_1M.get((provider or "").lower(), _PRICE_PER_1M["openai"])


def compute_cost(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    price = _price_per_1m(provider)
    return (prompt_tokens * price["prompt"] + completion_tokens * price["completion"]) / 1_000_000


class CostManager:
    async def record(
        self,
        *,
        provider: str,
        model: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        user_id: int | None = None,
        conversation_id: str | None = None,
        trace_id: str | None = None,
        agent_role: str = "",
        tool_name: str = "",
    ) -> float:
        """落一条 cost_records，返回本次成本 USD。DB 不可用时仅记进程内指标。"""
        cost = compute_cost(provider, prompt_tokens, completion_tokens)
        # 进程内指标（/metrics）
        try:
            from app.monitor.metrics import get_metrics

            get_metrics().record_request(
                provider=provider, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
            )
        except Exception:
            pass
        # 多维落库
        try:
            from app.db.session import SessionLocal
            from app.models.cost_record import CostRecord

            db = SessionLocal()
            try:
                db.add(CostRecord(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    trace_id=trace_id,
                    model=model,
                    provider=provider,
                    agent_role=agent_role,
                    tool_name=tool_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost,
                ))
                db.commit()
            finally:
                db.close()
        except Exception as exc:
            logger.warning(f"[Cost] 落库失败（已降级，仅进程内指标）: {exc}")
        return cost

    def check_daily_limit(self, user_id: int) -> tuple[bool, float, float]:
        """返回 (是否允许, 今日已花 USD, 日限额)；限额<=0 表示不限。"""
        limit = 0.0
        try:
            from app.services.system.settings_store import settings_store

            limit = float(settings_store.get("userDailyCostLimitUsd", 0) or 0)
        except Exception:
            limit = 0.0
        spent = self.today_cost(user_id)
        if limit <= 0:
            return True, spent, limit
        return spent < limit, spent, limit

    def today_cost(self, user_id: int) -> float:
        try:
            from sqlalchemy import func, select

            from app.db.session import SessionLocal
            from app.models.cost_record import CostRecord

            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            db = SessionLocal()
            try:
                return float(db.scalar(
                    select(func.coalesce(func.sum(CostRecord.cost_usd), 0.0)).where(
                        CostRecord.user_id == user_id, CostRecord.created_at >= start
                    )
                ) or 0.0)
            finally:
                db.close()
        except Exception:
            return 0.0

    def aggregate(self, *, days: int = 7) -> dict[str, Any]:
        """成本中心聚合：按天 / 模型 / Agent 角色出账。"""
        from sqlalchemy import func, select

        from app.db.session import SessionLocal
        from app.models.cost_record import CostRecord

        since = datetime.now() - timedelta(days=days)
        db = SessionLocal()
        try:
            def _group(col):
                rows = db.execute(
                    select(col, func.sum(CostRecord.cost_usd), func.sum(CostRecord.prompt_tokens + CostRecord.completion_tokens))
                    .where(CostRecord.created_at >= since)
                    .group_by(col)
                ).all()
                return [
                    {"groupKey": str(r[0] or "unknown"), "costUsd": round(float(r[1] or 0), 6), "tokens": int(r[2] or 0)}
                    for r in rows
                ]

            total = float(db.scalar(
                select(func.coalesce(func.sum(CostRecord.cost_usd), 0.0)).where(CostRecord.created_at >= since)
            ) or 0.0)
            return {
                "totalUsd": round(total, 6),
                "byModel": _group(CostRecord.model),
                "byProvider": _group(CostRecord.provider),
                "byAgentRole": _group(CostRecord.agent_role),
            }
        finally:
            db.close()


_cost_manager: CostManager | None = None


def get_cost_manager() -> CostManager:
    global _cost_manager
    if _cost_manager is None:
        _cost_manager = CostManager()
    return _cost_manager
