"""app/services/task/task_service.py — 异步任务服务（§14）

任务生命周期管理 + task_progress WS 推送（经 NotifyHub，协议已定义前端已声明）。
每个方法各自开启短事务，供后台 worker 与 API 共用。
"""

from __future__ import annotations

from typing import Any

from app.constants.status import TaskStatusEnum
from app.utils.logger import logger


class TaskService:
    def create(self, user_id: int, input_text: str, *, kind: str = "agent", title: str = "") -> str:
        from app.db.session import SessionLocal
        from app.models.agent_task import AgentTask

        db = SessionLocal()
        try:
            row = AgentTask(
                user_id=user_id,
                kind=kind,
                title=title or input_text[:60],
                input=input_text,
                status=TaskStatusEnum.PENDING.value,
                progress=0,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row.id
        finally:
            db.close()

    def get_raw(self, task_id: str):
        from app.db.session import SessionLocal
        from app.models.agent_task import AgentTask

        db = SessionLocal()
        try:
            row = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if row is not None:
                db.expunge(row)
            return row
        finally:
            db.close()

    def get(self, user_id: int, task_id: str) -> dict | None:
        from app.db.session import SessionLocal
        from app.models.agent_task import AgentTask

        db = SessionLocal()
        try:
            row = db.query(AgentTask).filter(
                AgentTask.id == task_id, AgentTask.user_id == user_id
            ).first()
            return self._to_dict(row) if row else None
        finally:
            db.close()

    def list_tasks(self, user_id: int, *, page: int = 1, size: int = 20) -> tuple[list[dict], int]:
        from app.db.session import SessionLocal
        from app.models.agent_task import AgentTask

        db = SessionLocal()
        try:
            base = db.query(AgentTask).filter(AgentTask.user_id == user_id)
            total = base.count()
            rows = (
                base.order_by(AgentTask.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all()
            )
            return [self._to_dict(r) for r in rows], total
        finally:
            db.close()

    # ---------- 状态迁移 ----------

    def _set(self, task_id: str, **fields: Any) -> None:
        from app.db.session import SessionLocal
        from app.models.agent_task import AgentTask

        db = SessionLocal()
        try:
            row = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if row is None:
                return
            for k, v in fields.items():
                setattr(row, k, v)
            db.commit()
        finally:
            db.close()

    def mark_running(self, task_id: str) -> None:
        self._set(task_id, status=TaskStatusEnum.RUNNING.value)

    def update_progress(self, task_id: str, progress: int) -> None:
        self._set(task_id, progress=max(0, min(100, progress)))

    def mark_success(self, task_id: str, result: str) -> None:
        self._set(task_id, status=TaskStatusEnum.SUCCESS.value, progress=100, result=result[:20000])

    def mark_failed(self, task_id: str, error: str) -> None:
        self._set(task_id, status=TaskStatusEnum.FAILED.value, error=error[:4000])

    # ---------- 进度推送 ----------

    async def push_progress(
        self, task_id: str, user_id: int, progress: int, detail: str, *, status: str = "running"
    ) -> None:
        """经 NotifyHub 推送 task_progress（前端 useNotifySocket 消费）。"""
        try:
            from app.services.system.notify_hub import get_notify_hub

            hub = await get_notify_hub()
            await hub.publish(user_id, {
                "type": "task_progress",
                "payload": {
                    "taskId": task_id,
                    "progress": progress,
                    "detail": detail,
                    "status": status,
                },
            })
        except Exception as exc:
            logger.warning(f"[TaskService] 进度推送失败: {exc}")

    @staticmethod
    def _to_dict(row) -> dict:
        return {
            "id": row.id,
            "kind": row.kind,
            "title": row.title,
            "input": row.input,
            "status": row.status,
            "progress": row.progress,
            "result": row.result,
            "error": row.error,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
