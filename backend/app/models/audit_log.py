"""backend/app/models/audit_log.py"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    module: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
