"""backend/app/models/message.py"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def new_message_id() -> str:
    return f"msg_{uuid.uuid4().hex}"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_message_id)
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    tools: Mapped[list | None] = mapped_column(JSON, nullable=True)

    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        "Conversation",
        back_populates="messages",
    )