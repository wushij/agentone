"""app/services/llm.py — LLM 服务"""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from app.llm.factory import create_chat_model


class LLMService:
    def __init__(self):
        self._model: BaseChatModel | None = None

    async def get_model(self, model_id: str | None = None) -> BaseChatModel:
        if self._model is None:
            self._model = create_chat_model(model=model_id)
        return self._model

    async def chat(self, messages: list[dict[str, str]], model_id: str | None = None) -> str:
        model = await self.get_model(model_id)
        from langchain_core.messages import HumanMessage, SystemMessage

        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            else:
                lc_messages.append(HumanMessage(content=msg["content"]))

        response = await model.ainvoke(lc_messages)
        return response.content if isinstance(response.content, str) else str(response.content)