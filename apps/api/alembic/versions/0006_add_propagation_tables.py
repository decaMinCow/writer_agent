"""add propagation engine tables

Revision ID: 0006_add_propagation_tables
Revises: 0005_add_kg_and_lint_tables
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0006_add_propagation_tables"
down_revision = "0005_add_kg_and_lint_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "propagation_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column(
            "base_artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "edited_artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=False,
        ),
        sa.Column("fact_changes", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_propagation_events_snapshot", "propagation_events", ["brief_snapshot_id"])
    op.create_index(
        "ix_propagation_events_edited_version", "propagation_events", ["edited_artifact_version_id"]
    )

    op.create_table(
        "artifact_impacts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "propagation_event_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("propagation_events.id"),
            nullable=False,
        ),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column(
            "artifact_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id"),
            nullable=False,
        ),
        sa.Column(
            "artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "repaired_artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=True,
        ),
        sa.Column(
            "repaired_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_artifact_impacts_snapshot", "artifact_impacts", ["brief_snapshot_id"])
    op.create_index("ix_artifact_impacts_artifact", "artifact_impacts", ["artifact_id"])
    op.create_index(
        "ix_artifact_impacts_event", "artifact_impacts", ["propagation_event_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_artifact_impacts_event", table_name="artifact_impacts")
    op.drop_index("ix_artifact_impacts_artifact", table_name="artifact_impacts")
    op.drop_index("ix_artifact_impacts_snapshot", table_name="artifact_impacts")
    op.drop_table("artifact_impacts")

    op.drop_index("ix_propagation_events_edited_version", table_name="propagation_events")
    op.drop_index("ix_propagation_events_snapshot", table_name="propagation_events")
    op.drop_table("propagation_events")

