"""app/runtime/scheduler/scheduler.py — 异步任务调度器（§14）

近期实现：进程内 asyncio 队列 + 后台 worker（远期可换 arq/Celery，接口不变）。
长任务：发起 → 立即返回 task_id → worker 后台跑 Runtime → task_progress WS 推送
→ 完成写 result + Artifact 交付 + 站内通知。断点续跑依托 checkpoint_thread_id。
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.utils.logger import logger

# 任务处理器签名：async (task_id, user_id, input, push) -> result_text
TaskHandler = Callable[[str, int, str, "ProgressPush"], Awaitable[str]]
ProgressPush = Callable[[int, str], Awaitable[None]]


class TaskScheduler:
    def __init__(self, concurrency: int = 2) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._handlers: dict[str, TaskHandler] = {}
        self._concurrency = concurrency
        self._running = False

    def register_handler(self, kind: str, handler: TaskHandler) -> None:
        self._handlers[kind] = handler

    async def submit(self, task_id: str) -> None:
        await self._queue.put(task_id)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        for i in range(self._concurrency):
            self._workers.append(asyncio.get_running_loop().create_task(self._worker(i)))
        logger.info(f"[Scheduler] 已启动 {self._concurrency} 个任务 worker")

    async def stop(self) -> None:
        self._running = False
        for w in self._workers:
            w.cancel()
        for w in self._workers:
            try:
                await w
            except asyncio.CancelledError:
                pass
        self._workers = []

    async def _worker(self, idx: int) -> None:
        from app.services.task.task_service import TaskService

        while self._running:
            try:
                task_id = await self._queue.get()
            except asyncio.CancelledError:
                break
            try:
                svc = TaskService()
                task = svc.get_raw(task_id)
                if task is None:
                    continue
                handler = self._handlers.get(task.kind) or self._handlers.get("agent")
                if handler is None:
                    svc.mark_failed(task_id, "无可用任务处理器")
                    continue

                svc.mark_running(task_id)
                await svc.push_progress(task_id, task.user_id, 5, "任务开始")

                async def push(progress: int, detail: str, _tid=task_id, _uid=task.user_id) -> None:
                    svc.update_progress(_tid, progress)
                    await svc.push_progress(_tid, _uid, progress, detail)

                result = await handler(task_id, task.user_id, task.input, push)
                svc.mark_success(task_id, result)
                await svc.push_progress(task_id, task.user_id, 100, "任务完成", status="success")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"[Scheduler] 任务 {task_id} 执行失败: {exc}")
                try:
                    from app.services.task.task_service import TaskService as _TS

                    _TS().mark_failed(task_id, str(exc))
                except Exception:
                    pass


_scheduler: TaskScheduler | None = None


def get_scheduler() -> TaskScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
