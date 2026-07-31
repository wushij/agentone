"""app/runtime/router/model_router.py — Model Router（§9.1）

按角色路由到不同模型，支持 fallback + 指数退避重试 + 可重试错误分类。
角色路由表来自 settings_store.modelRoles（管理后台可配置，热更新）：
    {"modelRoles": {"planner": ["gpt-4o","deepseek-chat"], "summary": ["qwen"], ...}}
未配置角色时回退默认模型（create_chat_model 原行为），保证任何环境可运行。
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.utils.logger import logger

# 可重试错误关键词（限流/超时/5xx 可重试；鉴权失败不可重试）
_RETRYABLE = ("timeout", "rate limit", "429", "500", "502", "503", "504", "overload")
_NON_RETRYABLE = ("401", "403", "invalid api key", "authentication")


def _role_models(role: str) -> list[str]:
    try:
        from app.services.system.settings_store import settings_store

        roles = settings_store.get("modelRoles", {}) or {}
        models = roles.get(role) or []
        return [str(m) for m in models if m]
    except Exception:
        return []


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    if any(k in msg for k in _NON_RETRYABLE):
        return False
    return any(k in msg for k in _RETRYABLE)


def create_model_for_role(role: str, *, fallback_model: str | None = None):
    """按角色取首选模型创建实例；无配置回退默认。返回 (llm, model_id)。"""
    from app.llm.factory import create_chat_model

    candidates = _role_models(role)
    if fallback_model:
        candidates = candidates + [fallback_model]
    for model_id in candidates:
        try:
            return create_chat_model(model=model_id), model_id
        except Exception as exc:
            logger.warning(f"[ModelRouter] 角色 {role} 模型 {model_id} 创建失败，尝试下一个: {exc}")
    return create_chat_model(model=fallback_model), fallback_model or "default"


async def ainvoke_with_fallback(
    role: str,
    messages: list,
    *,
    fallback_model: str | None = None,
    max_retries: int = 2,
) -> Any:
    """按角色路由 + fallback + 指数退避重试地调用模型。"""
    candidates = _role_models(role) or []
    if fallback_model and fallback_model not in candidates:
        candidates.append(fallback_model)
    if not candidates:
        candidates = [None]  # 默认模型

    last_exc: Exception | None = None
    from app.llm.factory import create_chat_model

    for model_id in candidates:
        for attempt in range(max_retries + 1):
            try:
                llm = create_chat_model(model=model_id)
                return await llm.ainvoke(messages)
            except Exception as exc:
                last_exc = exc
                if not _is_retryable(exc):
                    break  # 不可重试错误 → 直接切下一个候选
                await asyncio.sleep(min(2 ** attempt, 8))
        # 上报 fallback 事件（§11）
        try:
            from app.events.bus import event_bus
            from app.events.message import EventMessage

            await event_bus.publish(EventMessage(
                event_type="ModelFallback",
                data={"role": role, "failedModel": model_id or "default"},
                sender="model_router",
            ))
        except Exception:
            pass
    if last_exc:
        raise last_exc
    raise RuntimeError(f"ModelRouter: 角色 {role} 无可用模型")
