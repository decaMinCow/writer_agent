"""add brief messages

Revision ID: 0002_add_brief_messages
Revises: 0001_add_core_tables
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_add_brief_messages"
down_revision = "0001_add_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brief_messages",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("briefs.id"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", "system", name="brief_message_role"),
            nullable=False,
        ),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_brief_messages_brief_id", "brief_messages", ["brief_id"])
    op.create_index("ix_brief_messages_created_at", "brief_messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_brief_messages_created_at", table_name="brief_messages")
    op.drop_index("ix_brief_messages_brief_id", table_name="brief_messages")
    op.drop_table("brief_messages")
    bind = op.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS brief_message_role")
