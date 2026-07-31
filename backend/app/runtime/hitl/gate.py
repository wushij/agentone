"""app/runtime/hitl/gate.py — Human-in-the-Loop 审批闸门（§16.2）

高危工具执行前挂起，等待人工审批：
1. 创建进程内 Future（approval_id）；
2. 经 NotifyHub 推送 approval_required（前端弹确认卡片）；
3. await Future 或超时（默认拒绝）；
4. 审批 API resolve(approval_id, approved) 唤醒。

进程内实现（Scheduler / SSE 均在同进程）；多实例部署可换 Redis pub/sub 唤醒。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.utils.logger import logger

APPROVAL_TIMEOUT_S = 120.0


@dataclass
class PendingApproval:
    id: str
    user_id: int
    action: str
    payload: dict[str, Any]
    task_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApprovalGate:
    def __init__(self) -> None:
        self._futures: dict[str, asyncio.Future[bool]] = {}
        self._pending: dict[str, PendingApproval] = {}

    async def request(
        self, *, user_id: int, action: str, payload: dict[str, Any],
        task_id: str | None = None, timeout: float = APPROVAL_TIMEOUT_S,
    ) -> bool:
        """挂起等待审批；返回是否通过。超时视为拒绝。"""
        approval_id = f"appr_{uuid4().hex[:12]}"
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        self._futures[approval_id] = future
        self._pending[approval_id] = PendingApproval(
            id=approval_id, user_id=user_id, action=action, payload=payload, task_id=task_id,
        )
        await self._notify(user_id, approval_id, action, payload, task_id)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            logger.info(f"[HITL] 审批 {approval_id} 超时，默认拒绝")
            return False
        finally:
            self._futures.pop(approval_id, None)
            self._pending.pop(approval_id, None)

    def resolve(self, approval_id: str, approved: bool, *, user_id: int | None = None) -> bool:
        """审批 API 调用：唤醒等待中的工具执行。返回是否成功 resolve。"""
        pending = self._pending.get(approval_id)
        if pending is None:
            return False
        if user_id is not None and pending.user_id != user_id:
            return False
        future = self._futures.get(approval_id)
        if future and not future.done():
            future.set_result(approved)
            return True
        return False

    def list_pending(self, user_id: int) -> list[dict[str, Any]]:
        return [
            {
                "id": p.id, "action": p.action, "payload": p.payload,
                "taskId": p.task_id, "createdAt": p.created_at,
            }
            for p in self._pending.values() if p.user_id == user_id
        ]

    async def _notify(self, user_id: int, approval_id: str, action: str, payload: dict, task_id: str | None) -> None:
        try:
            from app.services.system.notify_hub import get_notify_hub

            hub = await get_notify_hub()
            await hub.publish(user_id, {
                "type": "approval_required",
                "payload": {
                    "approvalId": approval_id,
                    "action": action,
                    "detail": payload,
                    "taskId": task_id,
                },
            })
        except Exception as exc:
            logger.warning(f"[HITL] 审批通知推送失败: {exc}")


_gate: ApprovalGate | None = None


def get_approval_gate() -> ApprovalGate:
    global _gate
    if _gate is None:
        _gate = ApprovalGate()
    return _gate
