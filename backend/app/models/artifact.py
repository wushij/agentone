"""app/models/artifact.py — 产物表（§12.2）

Agent 的价值越来越体现在产物而非纯文本：代码/图表/文档/表格统一注册为
Artifact，前端右侧面板可预览、下载、多版本切换。
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def new_artifact_id() -> str:
    return f"art_{uuid.uuid4().hex}"


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_artifact_id)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    # markdown / html / code / image / csv / excel / pdf / mermaid / chart
    type: Mapped[str] = mapped_column(String(32), default="markdown")
    title: Mapped[str] = mapped_column(String(256), default="")
    content: Mapped[str] = mapped_column(Text, default="")  # 正文或 storage 引用
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)  # code 类型的语言
    conversation_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
