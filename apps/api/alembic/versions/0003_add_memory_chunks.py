"""add memory chunks

Revision ID: 0003_add_memory_chunks
Revises: 0002_add_brief_messages
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "0003_add_memory_chunks"
down_revision = "0002_add_brief_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "memory_chunks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column(
            "artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_memory_chunks_brief_snapshot_id", "memory_chunks", ["brief_snapshot_id"])
    op.create_index("ix_memory_chunks_artifact_version_id", "memory_chunks", ["artifact_version_id"])


def downgrade() -> None:
    op.drop_index("ix_memory_chunks_artifact_version_id", table_name="memory_chunks")
    op.drop_index("ix_memory_chunks_brief_snapshot_id", table_name="memory_chunks")
    op.drop_table("memory_chunks")

