"""app/memory/manager.py — 统一编排 Session / Summary / Vector / LongTerm"""

from __future__ import annotations

from typing import Any

from app.memory.long_term import LongTermMemory
from app.memory.session import SessionMemory
from app.memory.summary import SummaryMemory
from app.memory.vector import VectorMemory


class MemoryManager:
    """
    标准链路：
      Chat History → Summary → Memory → Knowledge
    本 Manager 负责前三段的进程内编排；Knowledge 仍走 RagService。
    """

    def __init__(self) -> None:
        self.session = SessionMemory()
        self.summary = SummaryMemory()
        self.vector = VectorMemory()
        self.long_term = LongTermMemory()

    async def sync_session_from_history(
        self,
        conversation_id: str,
        history: list[Any],
    ) -> None:
        """把 LangChain / dict 历史同步进 SessionMemory（不改变原 history）。"""
        items: list[dict[str, Any]] = []
        for msg in history or []:
            role = getattr(msg, "type", None) or getattr(msg, "role", None) or "user"
            if role == "human":
                role = "user"
            if role == "ai":
                role = "assistant"
            content = getattr(msg, "content", None)
            if content is None and isinstance(msg, dict):
                content = msg.get("content")
                role = msg.get("role") or role
            if content is None:
                continue
            items.append({"role": str(role), "content": str(content)})
        await self.session.replace(conversation_id, items)

    async def remember_turn(
        self,
        conversation_id: str,
        *,
        user_text: str,
        assistant_text: str = "",
    ) -> None:
        items = [{"role": "user", "content": user_text}]
        if assistant_text:
            items.append({"role": "assistant", "content": assistant_text})
        await self.session.save(conversation_id, items)
        # 同时写入向量片段，便于会话内检索
        await self.vector.save(
            conversation_id,
            [{"content": user_text, "metadata": {"role": "user"}}],
        )
        if assistant_text:
            await self.vector.save(
                conversation_id,
                [{"content": assistant_text, "metadata": {"role": "assistant"}}],
            )

    async def build_context_block(
        self,
        *,
        conversation_id: str,
        user_id: str = "",
        query: str = "",
    ) -> str:
        """生成可注入 Prompt 的记忆上下文（空则返回空串，不影响主链路）。"""
        parts: list[str] = []

        summary = await self.summary.get_text(conversation_id)
        if summary:
            parts.append(f"【会话摘要】\n{summary}")

        if user_id:
            facts = await self.long_term.load(user_id, limit=10)
            if facts:
                lines = "\n".join(f"- {f.get('content')}" for f in facts)
                parts.append(f"【用户长期记忆】\n{lines}")

        if query:
            hits = await self.vector.search(conversation_id, query, top_k=3)
            if hits:
                lines = "\n".join(f"- {h.get('text')}" for h in hits)
                parts.append(f"【相关历史片段】\n{lines}")

        return "\n\n".join(parts).strip()


_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    global _manager
    if _manager is None:
        _manager = MemoryManager()
    return _manager
