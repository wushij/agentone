"""backend/app/models/prompt.py"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    type: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
