"""app/services/task/task_service.py — 异步长任务调度与生命周期服务"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class AsyncTaskService:
    """异步长任务调度管理服务"""

    @staticmethod
    def create_task(user_id: int, title: str, conversation_id: str | None = None, task_type: str = "async_agent") -> dict[str, Any]:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task_data = {
            "id": task_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "title": title,
            "task_type": task_type,
            "status": "pending",
            "progress": 0,
            "current_step": "排队等待中",
            "result": None,
            "error": None,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        logger.info(f"[TaskService] 创建长任务 {task_id}: '{title}' (User:{user_id})")
        return task_data

    @staticmethod
    def update_task_progress(task_id: str, progress: int, current_step: str) -> None:
        logger.info(f"[TaskService] 任务 {task_id} 进度: {progress}% - {current_step}")

    @staticmethod
    def complete_task(task_id: str, result: Any) -> None:
        logger.info(f"[TaskService] 任务 {task_id} 执行完成")

    @staticmethod
    def fail_task(task_id: str, error: str) -> None:
        logger.error(f"[TaskService] 任务 {task_id} 失败: {error}")


TaskService = AsyncTaskService
