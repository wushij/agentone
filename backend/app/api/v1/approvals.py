"""backend/app/api/v1/approvals.py — HITL 人工审批（§16.2）"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.runtime.hitl import get_approval_gate
from app.utils.response import success

router = APIRouter(prefix="/approvals", tags=["人工审批"])


class ApprovalDecision(BaseModel):
    approved: bool


@router.get("")
def list_pending(user: User = Depends(get_current_user)):
    return success(get_approval_gate().list_pending(user.id))


@router.post("/{approval_id}")
def decide(approval_id: str, body: ApprovalDecision, user: User = Depends(get_current_user)):
    ok = get_approval_gate().resolve(approval_id, body.approved, user_id=user.id)
    return success({"resolved": ok, "approved": body.approved})
