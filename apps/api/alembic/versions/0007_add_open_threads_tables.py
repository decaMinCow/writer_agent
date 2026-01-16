"""add open threads tables

Revision ID: 0007_add_open_threads_tables
Revises: 0006_add_propagation_tables
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0007_add_open_threads_tables"
down_revision = "0006_add_propagation_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "open_threads",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_open_threads_snapshot", "open_threads", ["brief_snapshot_id"])
    op.create_index("ix_open_threads_status", "open_threads", ["status"])
    op.create_index("ix_open_threads_updated_at", "open_threads", ["updated_at"])

    op.create_table(
        "open_thread_refs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "thread_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("open_threads.id"),
            nullable=False,
        ),
        sa.Column(
            "artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=False,
        ),
        sa.Column("ref_kind", sa.String(length=32), nullable=False),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_open_thread_refs_thread", "open_thread_refs", ["thread_id"])
    op.create_index("ix_open_thread_refs_artifact_version", "open_thread_refs", ["artifact_version_id"])
    op.create_index("ix_open_thread_refs_ref_kind", "open_thread_refs", ["ref_kind"])


def downgrade() -> None:
    op.drop_index("ix_open_thread_refs_ref_kind", table_name="open_thread_refs")
    op.drop_index("ix_open_thread_refs_artifact_version", table_name="open_thread_refs")
    op.drop_index("ix_open_thread_refs_thread", table_name="open_thread_refs")
    op.drop_table("open_thread_refs")

    op.drop_index("ix_open_threads_updated_at", table_name="open_threads")
    op.drop_index("ix_open_threads_status", table_name="open_threads")
    op.drop_index("ix_open_threads_snapshot", table_name="open_threads")
    op.drop_table("open_threads")
