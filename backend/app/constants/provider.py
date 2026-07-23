"""app/constants/provider.py — 模型 Provider 枚举"""

from enum import Enum


class ProviderEnum(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    MOCK = "mock"
