"""app/providers/base.py — 模型提供商基类"""

from abc import ABC, abstractmethod

from langchain_core.language_models.chat_models import BaseChatModel


class BaseProvider(ABC):
    @abstractmethod
    def create_chat_model(
        self,
        model_name: str,
        api_key: str,
        base_url: str = "",
        temperature: float = 0.7,
        **kwargs,
    ) -> BaseChatModel:
        ...
