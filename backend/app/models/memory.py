"""app/models/memory.py — 持久记忆表（§7.2）"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MemoryEntry(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    scope: Mapped[str] = mapped_column(String(16), default="user")  # session / user / global
    kind: Mapped[str] = mapped_column(String(16), default="fact")  # fact / preference / episode / skill
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # 向量（JSON 存储）
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    pinned: Mapped[int] = mapped_column(Integer, default=0)  # 用户置顶（免衰减）
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
