"""会话标题自动生成"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.factory import create_chat_model

_TITLE_PROMPT = (
    "你是会话标题生成器。根据用户首条消息和助手首条回复，生成一条简洁的中文会话标题。"
    "要求：6-18 个字，概括主题，不要引号，不要句号，只输出标题本身。"
)


def fallback_conversation_title(user_message: str) -> str:
    text = " ".join(user_message.strip().split())
    if not text:
        return "新对话"
    if text.startswith("http://") or text.startswith("https://"):
        try:
            host = urlparse(text.split()[0]).netloc
            if host:
                return f"链接 · {host}"[:32]
        except Exception:
            pass
        return "链接咨询"
    return text[:24] + ("…" if len(text) > 24 else "")


def normalize_generated_title(raw: str, user_message: str) -> str:
    title = raw.strip().strip('"\'""''「」《》[]')
    title = re.sub(r"\s+", " ", title.split("\n")[0].strip())
    if not title or len(title) > 40:
        return fallback_conversation_title(user_message)
    return title[:32]


async def generate_conversation_title(
    user_message: str,
    assistant_message: str,
    *,
    model_id: str | None = None,
) -> str:
    if not assistant_message.strip():
        return fallback_conversation_title(user_message)

    try:
        llm = create_chat_model(model=model_id)
        resp = await llm.ainvoke(
            [
                SystemMessage(content=_TITLE_PROMPT),
                HumanMessage(
                    content=(
                        f"用户：{user_message[:400]}\n\n"
                        f"助手：{assistant_message[:400]}"
                    )
                ),
            ]
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content or "")
        return normalize_generated_title(content, user_message)
    except Exception:
        return fallback_conversation_title(user_message)
