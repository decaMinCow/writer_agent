"""add exports glossary tables

Revision ID: 0008_add_exports_glossary_tables
Revises: 0007_add_open_threads_tables
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0008_add_exports_glossary_tables"
down_revision = "0007_add_open_threads_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "snapshot_glossary_entries",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column("term", sa.String(length=255), nullable=False),
        sa.Column("replacement", sa.String(length=255), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_snapshot_glossary_entries_snapshot",
        "snapshot_glossary_entries",
        ["brief_snapshot_id"],
    )
    op.create_index("ix_snapshot_glossary_entries_term", "snapshot_glossary_entries", ["term"])


def downgrade() -> None:
    op.drop_index("ix_snapshot_glossary_entries_term", table_name="snapshot_glossary_entries")
    op.drop_index("ix_snapshot_glossary_entries_snapshot", table_name="snapshot_glossary_entries")
    op.drop_table("snapshot_glossary_entries")
