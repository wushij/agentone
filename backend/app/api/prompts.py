"""backend/app/api/prompts.py"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.common.response import success
from app.core.deps import require_permission
from app.db.session import get_db
from app.models.user import User
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/api/prompts", tags=["Prompt"])


class PromptCreateRequest(BaseModel):
    name: str
    content: str
    type: str = "custom"


class PromptUpdateRequest(BaseModel):
    content: str = Field(min_length=1)


class PromptStatusRequest(BaseModel):
    enabled: bool


@router.get("")
def list_prompts(user: User = Depends(require_permission("prompt:manage")), db: Session = Depends(get_db)):
    svc = PromptService(db)
    return success([svc.to_dict(p) for p in svc.list_prompts()])


@router.post("")
def create_prompt(
    body: PromptCreateRequest,
    user: User = Depends(require_permission("prompt:manage")),
    db: Session = Depends(get_db),
):
    svc = PromptService(db)
    row = svc.create(body.name, body.content, body.type)
    return success(svc.to_dict(row), message="创建成功")


@router.put("/{name}")
def update_prompt(
    name: str,
    body: PromptUpdateRequest,
    user: User = Depends(require_permission("prompt:manage")),
    db: Session = Depends(get_db),
):
    svc = PromptService(db)
    row = svc.update(name, body.content)
    if row is None:
        raise ValueError("Prompt 不存在")
    return success(svc.to_dict(row), message="保存成功")


@router.patch("/{name}/status")
def set_prompt_status(
    name: str,
    body: PromptStatusRequest,
    user: User = Depends(require_permission("prompt:manage")),
    db: Session = Depends(get_db),
):
    row = PromptService(db).set_enabled(name, body.enabled)
    if row is None:
        raise ValueError("Prompt 不存在")
    return success(PromptService(db).to_dict(row), message="状态已更新")


@router.delete("/{name}")
def delete_prompt(
    name: str,
    user: User = Depends(require_permission("prompt:manage")),
    db: Session = Depends(get_db),
):
    if not PromptService(db).delete(name):
        raise ValueError("Prompt 不存在")
    return success(None, message="已删除")


class PromptRollbackRequest(BaseModel):
    version: int


@router.get("/{name}/history")
def get_prompt_history(
    name: str,
    user: User = Depends(require_permission("prompt:manage")),
    db: Session = Depends(get_db),
):
    svc = PromptService(db)
    rows = svc.list_history(name)
    return success([
        {
            "id": r.id,
            "version": r.version,
            "content": r.content,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ])


@router.post("/{name}/rollback")
def rollback_prompt(
    name: str,
    body: PromptRollbackRequest,
    user: User = Depends(require_permission("prompt:manage")),
    db: Session = Depends(get_db),
):
    svc = PromptService(db)
    row = svc.rollback(name, body.version)
    if row is None:
        raise ValueError("历史版本不存在或回滚失败")
    return success(svc.to_dict(row), message="已回滚至选定版本")