"""app/providers/gemini.py — Gemini 模型提供商"""

from langchain_core.language_models.chat_models import BaseChatModel

from app.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    def create_chat_model(
        self,
        model_name: str,
        api_key: str,
        base_url: str = "",
        temperature: float = 0.7,
        **kwargs,
    ) -> BaseChatModel:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise ImportError(
                "langchain-google-genai is not installed. Run: pip install langchain-google-genai"
            ) from exc
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            **kwargs,
        )
