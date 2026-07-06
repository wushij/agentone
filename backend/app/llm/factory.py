"""backend/app/llm/factory.py"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.llm.mock import MockChatModel
from app.models.model_config import ModelConfig


def create_chat_model_from_config(cfg: ModelConfig, **kwargs) -> BaseChatModel:
    if cfg.provider == "mock":
        return MockChatModel()
    api_key = cfg.api_key
    base_url = cfg.base_url
    if cfg.provider == "deepseek" and not api_key:
        settings = get_settings()
        api_key = settings.DEEPSEEK_API_KEY
        base_url = base_url or settings.DEEPSEEK_BASE_URL
    if cfg.provider != "mock" and not api_key:
        raise ValueError(f"模型 {cfg.name} 未配置 API Key")
    
    streaming = kwargs.pop("streaming", True)
    return ChatOpenAI(
        model=cfg.model_name,
        api_key=api_key,
        base_url=base_url or None,
        temperature=float(cfg.temperature),
        streaming=streaming,
        **kwargs
    )


def create_chat_model(*, model: str | None = None, temperature: float | None = None) -> BaseChatModel:
    from app.db.session import SessionLocal
    from app.services.model_service import ModelService
    from app.services.settings_store import settings_store

    db = SessionLocal()
    try:
        svc = ModelService(db)
        cfg = svc.resolve_model(model)
        if cfg:
            temp = temperature
            if temp is None:
                temp = float(settings_store.get_all().get("defaultTemperature", cfg.temperature))
            return create_chat_model_from_config(cfg)
    finally:
        db.close()

    settings = get_settings()
    store = settings_store.get_all()
    model_name = model or store.get("defaultModel") or settings.DEEPSEEK_MODEL
    temp = temperature if temperature is not None else float(store.get("defaultTemperature", 0.7))

    if settings.LLM_PROVIDER == "deepseek" and settings.DEEPSEEK_API_KEY:
        return ChatOpenAI(
            model=model_name,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=temp,
            streaming=True,
        )
    return MockChatModel()