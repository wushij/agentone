"""backend/app/api/v1/memories.py — 「AI 记忆」用户可见可控（§7.2 合规刚需）"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.deps import get_current_user, require_admin
from app.memory.persistent import get_persistent_memory
from app.models.user import User
from app.utils.pagination import page_result
from app.utils.response import success

router = APIRouter(prefix="/memories", tags=["AI 记忆"])


class MemoryPinRequest(BaseModel):
    pinned: bool = True


@router.get("")
def list_memories(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    records, total = get_persistent_memory().list_memories(user.id, page=page, size=size)
    return success(page_result(records, total))


@router.delete("/{memory_id}")
def delete_memory(memory_id: int, user: User = Depends(get_current_user)):
    if not get_persistent_memory().delete_memory(user.id, memory_id):
        raise HTTPException(status_code=404, detail="记忆不存在")
    return success(None, message="已删除")


@router.put("/{memory_id}/pin")
def pin_memory(memory_id: int, body: MemoryPinRequest, user: User = Depends(get_current_user)):
    if not get_persistent_memory().set_pinned(user.id, memory_id, body.pinned):
        raise HTTPException(status_code=404, detail="记忆不存在")
    return success(None, message="已置顶" if body.pinned else "已取消置顶")


@router.post("/decay")
def trigger_decay(user: User = Depends(require_admin)):
    """手动触发遗忘衰减（定时任务已自动运行，此接口供运维/调试）。"""
    result = get_persistent_memory().decay()
    return success(result, message=f"衰减 {result['decayed']} 条，清理 {result['removed']} 条")
