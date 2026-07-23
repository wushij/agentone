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
    return _PROVIDERS.get(key) or _PROVIDERS["openai"]


def list_providers() -> list[str]:
    return sorted(_PROVIDERS.keys())


__all__ = ["BaseProvider", "get_provider", "list_providers"]
