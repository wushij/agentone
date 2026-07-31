"""app/models/knowledge_base.py — 知识库元数据表（§8.1 元数据入 MySQL）

config JSON 列保存全部检索配置（fileIds/chunkSize/retrievalMode/topK/...），
对外仍以 dict 形态提供，兼容原 knowledge.json 条目结构。
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # kb_xxxxxxxx
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
