"""app/services/prompt/prompt_ab.py — Prompt A/B Test（§10.2）

一个 Prompt 域可同时激活两个版本，按流量比例分配；每次解析记录命中的版本
（写入 metrics + 供 trace 关联），配合 Evaluator 输出版本对比报告。

配置来自 settings_store.promptExperiments：
  {"planner": {"variantVersion": 3, "ratioB": 0.1}}
表示 planner 域有 10% 流量走历史版本 3（B 组），其余走当前版本（A 组）。
未配置则始终返回当前内容（A 组），零开销。
"""

from __future__ import annotations

import random


def resolve_prompt(name: str, fallback: str = "") -> tuple[str, str]:
    """返回 (content, variant_label)；variant_label 形如 'A:v5' / 'B:v3'。"""
    try:
        from app.db.session import SessionLocal
        from app.services.prompt.prompt_service import PromptService
        from app.services.system.settings_store import settings_store

        experiments = settings_store.get("promptExperiments", {}) or {}
        exp = experiments.get(name)

        db = SessionLocal()
        try:
            svc = PromptService(db)
            row = svc.get_by_name(name)
            current = (row.content if row and row.enabled == 1 else "") or ""
            current_ver = row.version if row else 1

            if exp and isinstance(exp, dict):
                ratio_b = float(exp.get("ratioB", 0) or 0)
                variant_version = exp.get("variantVersion")
                if variant_version and 0 < ratio_b <= 1 and random.random() < ratio_b:
                    from app.models.prompt_history import PromptHistory
                    from sqlalchemy import select

                    hist = db.scalar(
                        select(PromptHistory).where(
                            PromptHistory.prompt_name == name,
                            PromptHistory.version == int(variant_version),
                        )
                    )
                    if hist:
                        _record_hit(name, f"B:v{variant_version}")
                        return hist.content, f"B:v{variant_version}"

            if current:
                _record_hit(name, f"A:v{current_ver}")
                return current, f"A:v{current_ver}"
        finally:
            db.close()
    except Exception:
        pass
    return fallback, "fallback"


def _record_hit(name: str, variant: str) -> None:
    try:
        from app.monitor.metrics import get_metrics

        get_metrics().record_cache(f"prompt_ab:{name}:{variant}", hit=True)
    except Exception:
        pass
