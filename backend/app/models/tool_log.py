"""backend/app/models/tool_log.py"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ToolLog(Base):
    __tablename__ = "tool_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), index=True)
    tool_name: Mapped[str] = mapped_column(String(64))
    params: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
