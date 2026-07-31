"""stage3 batch1 — agent_tasks / artifacts

Revision ID: 0003_stage3_tasks_artifacts
Revises: 0002_stage2_tables
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_stage3_tasks_artifacts"
down_revision = "0002_stage2_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if "agent_tasks" not in existing:
        op.create_table(
            "agent_tasks",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("user_id", sa.BigInteger, nullable=False),
            sa.Column("kind", sa.String(32), nullable=False, server_default="agent"),
            sa.Column("title", sa.String(256), nullable=False, server_default=""),
            sa.Column("input", sa.Text, nullable=False),
            sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
            sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
            sa.Column("result", sa.Text, nullable=True),
            sa.Column("error", sa.Text, nullable=True),
            sa.Column("checkpoint_thread_id", sa.String(64), nullable=True),
            sa.Column("task_metadata", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index("ix_agent_tasks_user_id", "agent_tasks", ["user_id"])
        op.create_index("ix_agent_tasks_status", "agent_tasks", ["status"])

    if "artifacts" not in existing:
        op.create_table(
            "artifacts",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("user_id", sa.BigInteger, nullable=False),
            sa.Column("type", sa.String(32), nullable=False, server_default="markdown"),
            sa.Column("title", sa.String(256), nullable=False, server_default=""),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("language", sa.String(32), nullable=True),
            sa.Column("conversation_id", sa.String(64), nullable=True),
            sa.Column("message_id", sa.String(64), nullable=True),
            sa.Column("task_id", sa.String(64), nullable=True),
            sa.Column("version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index("ix_artifacts_user_id", "artifacts", ["user_id"])
        op.create_index("ix_artifacts_conversation_id", "artifacts", ["conversation_id"])
        op.create_index("ix_artifacts_task_id", "artifacts", ["task_id"])


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("agent_tasks")
