"""backend/app/services/audit_log_service.py"""

from __future__ import annotations

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def write(
        self,
        *,
        user_id: int | None,
        module: str,
        action: str,
        detail: str = "",
        status: str = "success",
    ) -> None:
        self.db.add(
            AuditLog(
                user_id=user_id,
                module=module,
                action=action,
                detail=detail[:4000],
                status=status,
            )
        )
        self.db.commit()

    def list_logs(
        self,
        *,
        user_id: int | None = None,
        module: str | None = None,
        modules: set[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)
        if module:
            stmt = stmt.where(AuditLog.module == module)
            count_stmt = count_stmt.where(AuditLog.module == module)
        if modules:
            stmt = stmt.where(AuditLog.module.in_(modules))
            count_stmt = count_stmt.where(AuditLog.module.in_(modules))
        total = int(self.db.scalar(count_stmt) or 0)
        rows = (
            self.db.scalars(
                stmt.order_by(desc(AuditLog.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .all()
        )
        return list(rows), total

    def delete_log(self, log_id: int, *, user_id: int | None = None) -> bool:
        row = self.db.get(AuditLog, log_id)
        if row is None:
            return False
        if user_id is not None and row.user_id != user_id:
            return False
        self.db.delete(row)
        self.db.commit()
        return True
