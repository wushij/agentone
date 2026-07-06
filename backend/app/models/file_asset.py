"""backend/app/models/file_asset.py"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def new_file_id() -> str:
    return f"file_{uuid.uuid4().hex}"


class FileAsset(Base):
    __tablename__ = "file_assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_file_id)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(256))
    original_name: Mapped[str] = mapped_column(String(256))
    mime_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    category: Mapped[str] = mapped_column(String(32), default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
