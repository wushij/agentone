"""app/providers/__init__.py — LLM provider registry"""

from __future__ import annotations

from app.providers.base import BaseProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider

_PROVIDERS: dict[str, BaseProvider] = {
    "deepseek": DeepSeekProvider(),
    "openai": OpenAIProvider(),
    "qwen": OpenAIProvider(),  # OpenAI-compatible
    "gemini": GeminiProvider(),
    "ollama": OllamaProvider(),
}


def get_provider(name: str) -> BaseProvider:
    key = (name or "openai").lower().strip()
    provider = _PROVIDERS.get(key)
    if provider is None:
        # 修复（§4.9）：未知 provider 名不再静默回退，至少告警提示配置可能写错。
        from app.utils.logger import logger

        logger.warning(f"[Provider] 未知 provider 名「{name}」，已回退 OpenAI 兼容实现，请核对模型配置")
        return _PROVIDERS["openai"]
    return provider


def list_providers() -> list[str]:
    return sorted(_PROVIDERS.keys())


__all__ = ["BaseProvider", "get_provider", "list_providers"]
