"""backend/app/models/prompt_history.py"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromptHistory(Base):
    __tablename__ = "prompt_histories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prompt_name: Mapped[str] = mapped_column(String(128), index=True)
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
