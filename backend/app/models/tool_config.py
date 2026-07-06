"""backend/app/models/tool_config.py"""

from datetime import datetime

from sqlalchemy import DateTime, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ToolConfig(Base):
    __tablename__ = "tool_configs"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(Text, default="")
    tool_type: Mapped[str] = mapped_column(String(32), default="builtin")
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
