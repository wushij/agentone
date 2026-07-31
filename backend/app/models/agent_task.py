"""app/models/agent_task.py — 异步任务表（§14）

长任务超出一次 HTTP 生命周期：发起 → 立即返回 task_id → 后台执行 →
task_progress 推送 → 完成发 TaskFinished + Artifact 交付。
checkpoint_thread_id 关联 LangGraph thread，支持断点续跑。
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def new_task_id() -> str:
    return f"task_{uuid.uuid4().hex}"


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_task_id)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    kind: Mapped[str] = mapped_column(String(32), default="agent")  # agent / report / scheduled
    title: Mapped[str] = mapped_column(String(256), default="")
    input: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)  # TaskStatusEnum
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0~100
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    checkpoint_thread_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    task_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
