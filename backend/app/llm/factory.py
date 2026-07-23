"""app/llm/factory.py — Create chat models via providers + DB config"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.llm.mock import MockChatModel
from app.models.model_config import ModelConfig
from app.providers import get_provider
from app.config.settings import get_settings


def create_chat_model_from_config(cfg: ModelConfig, **kwargs) -> BaseChatModel:
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
    provider = get_provider(cfg.provider)
    return provider.create_chat_model(
        model_name=cfg.model_name,
        api_key=api_key or "",
        base_url=base_url,
        temperature=float(cfg.temperature),
        streaming=streaming,
        **kwargs,
    )


def create_chat_model(*, model: str | None = None, temperature: float | None = None) -> BaseChatModel:
    from app.db.session import SessionLocal
    from app.services.llm.model_service import ModelService
    from app.services.system.settings_store import settings_store

    db = SessionLocal()
    try:
        svc = ModelService(db)
        cfg = svc.resolve_model(model)
        if cfg:
            return create_chat_model_from_config(cfg)
    finally:
        db.close()

    settings = get_settings()
    store = settings_store.get_all()
    model_name = model or store.get("defaultModel") or settings.DEEPSEEK_MODEL
    temp = temperature if temperature is not None else float(store.get("defaultTemperature", 0.7))

    if settings.LLM_PROVIDER == "deepseek" and settings.DEEPSEEK_API_KEY:
        provider = get_provider("deepseek")
        return provider.create_chat_model(
            model_name=model_name,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=temp,
            streaming=True,
        )
    return MockChatModel()
