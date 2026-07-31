"""backend/app/api/v1/tasks.py — 异步任务中心（§14）"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.runtime.scheduler import get_scheduler
from app.services.task.task_service import TaskService
from app.utils.pagination import page_result
from app.utils.response import success

router = APIRouter(prefix="/tasks", tags=["异步任务"])


class TaskCreateRequest(BaseModel):
    input: str = Field(description="任务描述/指令")
    title: str = Field(default="", description="可选任务标题")
    kind: str = Field(default="agent", description="任务类型")


@router.post("")
async def create_task(body: TaskCreateRequest, user: User = Depends(get_current_user)):
    text = body.input.strip()
    if not text:
        raise HTTPException(status_code=400, detail="任务内容不能为空")
    svc = TaskService()
    task_id = svc.create(user.id, text, kind=body.kind, title=body.title)
    await get_scheduler().submit(task_id)
    return success({"taskId": task_id}, message="任务已提交，后台执行中")


@router.get("")
def list_tasks(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    records, total = TaskService().list_tasks(user.id, page=page, size=size)
    return success(page_result(records, total))


@router.get("/{task_id}")
def get_task(task_id: str, user: User = Depends(get_current_user)):
    task = TaskService().get(user.id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success(task)
