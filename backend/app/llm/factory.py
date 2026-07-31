"""app/llm/factory.py — Create chat models via providers + DB config"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.llm.mock import MockChatModel
from app.models.model_config import ModelConfig
from app.providers import get_provider
from app.config.settings import get_settings


def _nudge_temperature(base: float, thinking_level: str) -> float:
    """扩展思考档位→温度微调：快速更确定、深度更严谨。"""
    if thinking_level == "fast":
        return max(0.0, min(base, 0.3))
    if thinking_level == "extended":
        return max(0.0, round(base * 0.8, 3))
    return base


def create_chat_model_from_config(cfg: ModelConfig, *, thinking_level: str = "standard", temperature: float | None = None, **kwargs) -> BaseChatModel:
    if cfg.provider == "mock":
        return MockChatModel()
    api_key = cfg.api_key
    base_url = cfg.base_url or ""
    if cfg.provider == "deepseek" and not api_key:
        settings = get_settings()
        api_key = settings.DEEPSEEK_API_KEY
        base_url = base_url or settings.DEEPSEEK_BASE_URL
    if cfg.provider != "mock" and not api_key:
        raise ValueError(f"模型 {cfg.name} 未配置 API Key")

    streaming = kwargs.pop("streaming", True)
    # 修复（§4.9）：显式 temperature 入参优先于 cfg.temperature
    base_temp = float(temperature if temperature is not None else cfg.temperature)
    provider = get_provider(cfg.provider)
    return provider.create_chat_model(
        model_name=cfg.model_name,
        api_key=api_key or "",
        base_url=base_url,
        temperature=_nudge_temperature(base_temp, thinking_level),
        streaming=streaming,
        **kwargs,
    )


def create_chat_model(*, model: str | None = None, temperature: float | None = None, thinking_level: str = "standard") -> BaseChatModel:
    from app.db.session import SessionLocal
    from app.services.llm.model_service import ModelService
    from app.services.system.settings_store import settings_store

    db = SessionLocal()
    try:
        svc = ModelService(db)
        cfg = svc.resolve_model(model)
        if cfg:
            return create_chat_model_from_config(cfg, thinking_level=thinking_level, temperature=temperature)
    finally:
        db.close()

    settings = get_settings()
    store = settings_store.get_all()
    model_name = model or store.get("defaultModel") or settings.DEEPSEEK_MODEL
    temp = temperature if temperature is not None else float(store.get("defaultTemperature", 0.7))
    temp = _nudge_temperature(temp, thinking_level)

    if settings.LLM_PROVIDER == "deepseek" and settings.DEEPSEEK_API_KEY:
        provider = get_provider("deepseek")
        return provider.create_chat_model(
            model_name=model_name,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=temp,
            streaming=True,
        )
    # 修复（§4.9）：非 mock 的 LLM_PROVIDER 却无可用配置→降级 Mock 时告警，避免“配了却仍 Mock”静默轷惑
    if settings.LLM_PROVIDER and settings.LLM_PROVIDER != "mock":
        from app.utils.logger import logger

        logger.warning(
            f"[Factory] LLM_PROVIDER={settings.LLM_PROVIDER} 但无可用模型配置/密钥，已降级 Mock；请在管理后台配置模型或补充 API Key"
        )
    return MockChatModel()
