"""app/providers/ollama.py — Ollama 模型提供商"""

from langchain_core.language_models.chat_models import BaseChatModel

from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    def create_chat_model(
        self,
        model_name: str,
        api_key: str = "",
        base_url: str = "",
        temperature: float = 0.7,
        **kwargs,
    ) -> BaseChatModel:
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise ImportError(
                "langchain-ollama is not installed. Run: pip install langchain-ollama"
            ) from exc
        return ChatOllama(
            model=model_name,
            base_url=base_url or "http://localhost:11434",
            temperature=temperature,
            **kwargs,
        )
