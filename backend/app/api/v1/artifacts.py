"""backend/app/api/v1/artifacts.py — 产物 API（§12.2）"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.runtime.artifacts import get_artifact_manager
from app.utils.response import success

router = APIRouter(prefix="/artifacts", tags=["产物"])


@router.get("")
def list_artifacts(
    conversationId: str = Query(default=""),
    taskId: str = Query(default=""),
    user: User = Depends(get_current_user),
):
    mgr = get_artifact_manager()
    if taskId:
        return success(mgr.list_by_task(user.id, taskId))
    if conversationId:
        return success(mgr.list_by_conversation(user.id, conversationId))
    return success([])


@router.get("/{artifact_id}")
def get_artifact(artifact_id: str, user: User = Depends(get_current_user)):
    art = get_artifact_manager().get(user.id, artifact_id)
    if art is None:
        raise HTTPException(status_code=404, detail="产物不存在")
    return success(art)
