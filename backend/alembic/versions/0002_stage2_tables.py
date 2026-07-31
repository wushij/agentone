"""stage2 — 阶段2新表：memories / cost_records / knowledge_bases

Revision ID: 0002_stage2_tables
Revises: 0001_baseline
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_stage2_tables"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if "memories" not in existing:
        op.create_table(
            "memories",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
            sa.Column("scope", sa.String(16), nullable=False, server_default="user"),
            sa.Column("kind", sa.String(16), nullable=False, server_default="fact"),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("embedding", sa.JSON, nullable=True),
            sa.Column("importance", sa.Float, nullable=False, server_default="0.5"),
            sa.Column("access_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("pinned", sa.Integer, nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("last_accessed_at", sa.DateTime, nullable=True),
            sa.Column("expires_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_memories_user_id", "memories", ["user_id"])

    if "cost_records" not in existing:
        op.create_table(
            "cost_records",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.BigInteger, nullable=True),
            sa.Column("conversation_id", sa.String(64), nullable=True),
            sa.Column("trace_id", sa.String(64), nullable=True),
            sa.Column("model", sa.String(128), nullable=False, server_default=""),
            sa.Column("provider", sa.String(32), nullable=False, server_default=""),
            sa.Column("agent_role", sa.String(32), nullable=False, server_default=""),
            sa.Column("tool_name", sa.String(64), nullable=False, server_default=""),
            sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
            sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
            sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index("ix_cost_records_user_id", "cost_records", ["user_id"])
        op.create_index("ix_cost_records_conversation_id", "cost_records", ["conversation_id"])
        op.create_index("ix_cost_records_trace_id", "cost_records", ["trace_id"])
        op.create_index("ix_cost_records_provider", "cost_records", ["provider"])
        op.create_index("ix_cost_records_created_at", "cost_records", ["created_at"])

    if "knowledge_bases" not in existing:
        op.create_table(
            "knowledge_bases",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("description", sa.Text, nullable=False),
            sa.Column("config", sa.JSON, nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index("ix_knowledge_bases_name", "knowledge_bases", ["name"])


def downgrade() -> None:
    op.drop_table("knowledge_bases")
    op.drop_table("cost_records")
    op.drop_table("memories")
