"""app/providers/deepseek.py — DeepSeek 模型提供商"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.providers.base import BaseProvider


class DeepSeekProvider(BaseProvider):
    def create_chat_model(
        self,
        model_name: str,
        api_key: str,
        base_url: str = "",
        temperature: float = 0.7,
        **kwargs,
    ) -> BaseChatModel:
        streaming = kwargs.pop("streaming", True)
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url or "https://api.deepseek.com",
            temperature=temperature,
            streaming=streaming,
            **kwargs,
        )
