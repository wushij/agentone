"""backend/app/api/tools.py"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.response import success
from app.core.deps import require_permission
from app.db.session import get_db
from app.models.user import User
from app.services.tool_service import ToolService

router = APIRouter(prefix="/api/tools", tags=["Tool"])


class ToolUpdateRequest(BaseModel):
    description: str | None = None
    status: str | None = None


@router.get("")
def list_tool_items(user: User = Depends(require_permission("tool:manage")), db: Session = Depends(get_db)):
    return success(ToolService(db).list_tools())


@router.put("/{name}")
def update_tool(
    name: str,
    body: ToolUpdateRequest,
    user: User = Depends(require_permission("tool:manage")),
    db: Session = Depends(get_db),
):
    row = ToolService(db).update(name, body.model_dump(exclude_none=True))
    if row is None:
        raise ValueError("工具不存在")
    return success(
        {
            "name": row.name,
            "description": row.description,
            "type": row.tool_type,
            "status": "enabled" if row.enabled == 1 else "disabled",
        },
        message="更新成功",
    )


@router.patch("/{name}/status")
def toggle_tool(
    name: str,
    enabled: bool,
    user: User = Depends(require_permission("tool:manage")),
    db: Session = Depends(get_db),
):
    row = ToolService(db).set_enabled(name, enabled)
    return success(
        {"name": row.name, "status": "enabled" if row.enabled == 1 else "disabled"},
        message="状态已更新",
    )

