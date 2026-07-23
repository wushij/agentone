"""app/repositories/audit_log_repository.py — 审计日志仓储"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):

    def __init__(self):
        super().__init__(AuditLog)

    def get_logs(
        self, db: Session, *, skip: int = 0, limit: int = 50
    ) -> Sequence[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.id.desc()).offset(skip).limit(limit)
        return db.scalars(stmt).all()


audit_log_repository = AuditLogRepository()
