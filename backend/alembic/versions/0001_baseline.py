"""baseline — 收编现有全部表结构为迁移基线

现有库（由 sql/init.sql + migrations/*.sql 建立）执行 `alembic stamp head` 收编；
全新库执行 `alembic upgrade head` 时按 ORM 元数据建表。
后续所有新表/字段变更一律通过 alembic revision 管理，禁止手写 SQL 直接改库。

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa  # noqa: F401

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 基线：按 ORM 元数据补齐缺失的表（已有表跳过，等价于 create_all 的幂等语义）
    from app.models.base import Base
    import app.models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    # 基线不支持回滚（避免误删生产数据）
    raise NotImplementedError("baseline 迁移不可回滚")
