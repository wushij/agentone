"""backend/app/api/logs.py"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.common.pagination import clamp_page, page_result
from app.common.response import success
from app.core.deps import require_permission
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.tool_log import ToolLog
from app.models.user import User
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/api/logs", tags=["日志中心"])


def _fmt_audit(row: AuditLog) -> dict:
    return {
        "id": row.id,
        "time": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "module": row.module,
        "type": row.action,
        "status": row.status,
        "message": row.detail or "",
    }


def _fmt_tool(row: ToolLog) -> dict:
    return {
        "id": row.id,
        "time": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "module": "tool",
        "type": row.tool_name,
        "status": getattr(row, "status", "success") or "success",
        "message": (row.result or row.params or "")[:200],
        "durationMs": row.duration_ms,
    }


_USER_MODULES = {"auth", "chat", "file", "profile", "user"}


def _query_logs(
    log_type: str,
    user: User,
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    if log_type == "tool":
        where = ToolLog.user_id == user.id
        total = int(db.scalar(select(func.count()).select_from(ToolLog).where(where)) or 0)
        stmt = (
            select(ToolLog)
            .where(where)
            .order_by(desc(ToolLog.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = db.scalars(stmt).all()
        return [_fmt_tool(r) for r in rows], total

    if log_type == "user":
        rows, total = AuditLogService(db).list_logs(
            user_id=user.id,
            modules=_USER_MODULES,
            page=page,
            page_size=page_size,
        )
        return [_fmt_audit(r) for r in rows], total

    if log_type == "agent":
        rows, total = AuditLogService(db).list_logs(
            user_id=user.id,
            module="agent",
            page=page,
            page_size=page_size,
        )
        return [_fmt_audit(r) for r in rows], total

    rows, total = AuditLogService(db).list_logs(
        user_id=user.id,
        module="system",
        page=page,
        page_size=page_size,
    )
    return [_fmt_audit(r) for r in rows], total


@router.get("")
def list_logs(
    log_type: str = Query(default="tool", alias="type"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100, alias="pageSize"),
    user: User = Depends(require_permission("log:read")),
    db: Session = Depends(get_db),
):
    page, size = clamp_page(page, size)
    items, total = _query_logs(log_type, user, db, page=page, page_size=size)
    return success(page_result(items, total))


@router.get("/export")
def export_logs(
    log_type: str = Query(default="tool", alias="type"),
    user: User = Depends(require_permission("log:read")),
    db: Session = Depends(get_db),
):
    items, _ = _query_logs(log_type, user, db, page=1, page_size=500)
    lines = [f"# AgentOne 日志导出 ({log_type})", ""]
    for row in items:
        lines.append(f"- [{row.get('time')}] {row.get('module')}/{row.get('type')} ({row.get('status')})")
        lines.append(f"  {row.get('message', '')}")
    content = "\n".join(lines)
    return PlainTextResponse(
        content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="logs_{log_type}.txt"'},
    )


@router.delete("/clear")
def clear_all_logs(
    log_type: str = Query(default="tool", alias="type"),
    user: User = Depends(require_permission("log:read")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import delete
    if log_type == "tool":
        db.execute(delete(ToolLog).where(ToolLog.user_id == user.id))
        db.commit()
        return success(None, message="所有 Tool 日志已清空")

    if log_type == "user":
        db.execute(delete(AuditLog).where(AuditLog.user_id == user.id, AuditLog.module.in_(_USER_MODULES)))
    elif log_type == "agent":
        db.execute(delete(AuditLog).where(AuditLog.user_id == user.id, AuditLog.module == "agent"))
    else:
        db.execute(delete(AuditLog).where(AuditLog.user_id == user.id, AuditLog.module == "system"))

    db.commit()
    return success(None, message="所有审计日志已清空")


@router.delete("/{log_id}")
def delete_log(
    log_id: int,
    log_type: str = Query(default="tool", alias="type"),
    user: User = Depends(require_permission("log:read")),
    db: Session = Depends(get_db),
):
    if log_type == "tool":
        row = db.get(ToolLog, log_id)
        if row is None or row.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")
        db.delete(row)
        db.commit()
        return success(None, message="删除成功")

    module_filter: str | None
    if log_type == "user":
        module_filter = None
    elif log_type == "agent":
        module_filter = "agent"
    else:
        module_filter = "system"

    service = AuditLogService(db)
    row = db.get(AuditLog, log_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")

    if log_type == "user":
        if row.module not in {"auth", "chat", "file", "profile", "user"}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")
    elif module_filter and row.module != module_filter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")

    if not service.delete_log(log_id, user_id=user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")
    return success(None, message="删除成功")
