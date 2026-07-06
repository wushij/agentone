"""backend/app/models/user.py"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(128))
    nickname: Mapped[str | None] = mapped_column(String(64))
    avatar: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(32), default="user")
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
