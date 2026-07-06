"""backend/app/models/conversation.py"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_conversation_id() -> str:
    return f"conv_{uuid.uuid4().hex}"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_conversation_id)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    is_archived: Mapped[int] = mapped_column(SmallInteger, default=0)

    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
