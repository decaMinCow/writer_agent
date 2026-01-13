"""add knowledge graph and lint tables

Revision ID: 0005_add_kg_and_lint_tables
Revises: 0004_add_app_settings
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_add_kg_and_lint_tables"
down_revision = "0004_add_app_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kg_entities",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_kg_entities_snapshot", "kg_entities", ["brief_snapshot_id"])
    op.create_index("ix_kg_entities_name", "kg_entities", ["name"])

    op.create_table(
        "kg_relations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column(
            "subject_entity_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kg_entities.id"),
            nullable=False,
        ),
        sa.Column("predicate", sa.String(length=64), nullable=False),
        sa.Column(
            "object_entity_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kg_entities.id"),
            nullable=False,
        ),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_kg_relations_snapshot", "kg_relations", ["brief_snapshot_id"])
    op.create_index("ix_kg_relations_subject", "kg_relations", ["subject_entity_id"])
    op.create_index("ix_kg_relations_object", "kg_relations", ["object_entity_id"])

    op.create_table(
        "kg_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column("event_key", sa.String(length=128), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("time_hint", sa.String(length=128), nullable=True),
        sa.Column(
            "artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=True,
        ),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_kg_events_snapshot", "kg_events", ["brief_snapshot_id"])
    op.create_index("ix_kg_events_artifact_version", "kg_events", ["artifact_version_id"])

    op.create_table(
        "lint_issues",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "artifact_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact_versions.id"),
            nullable=True,
        ),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_lint_issues_snapshot", "lint_issues", ["brief_snapshot_id"])
    op.create_index("ix_lint_issues_severity", "lint_issues", ["severity"])
    op.create_index("ix_lint_issues_artifact_version", "lint_issues", ["artifact_version_id"])


def downgrade() -> None:
    op.drop_index("ix_lint_issues_artifact_version", table_name="lint_issues")
    op.drop_index("ix_lint_issues_severity", table_name="lint_issues")
    op.drop_index("ix_lint_issues_snapshot", table_name="lint_issues")
    op.drop_table("lint_issues")

    op.drop_index("ix_kg_events_artifact_version", table_name="kg_events")
    op.drop_index("ix_kg_events_snapshot", table_name="kg_events")
    op.drop_table("kg_events")

    op.drop_index("ix_kg_relations_object", table_name="kg_relations")
    op.drop_index("ix_kg_relations_subject", table_name="kg_relations")
    op.drop_index("ix_kg_relations_snapshot", table_name="kg_relations")
    op.drop_table("kg_relations")

    op.drop_index("ix_kg_entities_name", table_name="kg_entities")
    op.drop_index("ix_kg_entities_snapshot", table_name="kg_entities")
    op.drop_table("kg_entities")
