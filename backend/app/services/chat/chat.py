"""app/services/chat.py — 聊天服务"""

from typing import Any

from app.core.engine.engine import get_engine
from app.services.llm.llm import LLMService


class ChatService:
    def __init__(self):
        self.llm_service = LLMService()

    async def send_message(self, user_input: str, **kwargs: Any) -> dict[str, Any]:
        engine = get_engine()
        result = await engine.invoke(user_input, **kwargs)
        return {
            "answer": result.get("final_answer", ""),
            "conversation_id": result.get("conversation_id", ""),
            "message_id": result.get("message_id", ""),
        }