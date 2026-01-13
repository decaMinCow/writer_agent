"""add core tables

Revision ID: 0001_add_core_tables
Revises:
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_add_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "briefs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )

    op.create_table(
        "brief_snapshots",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("briefs.id"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_brief_snapshots_brief_id", "brief_snapshots", ["brief_id"])

    op.create_table(
        "artifacts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "kind",
            sa.Enum("novel_chapter", "script_scene", name="artifact_kind"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "kind",
            sa.Enum("novel", "script", "novel_to_script", name="workflow_kind"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "running",
                "paused",
                "succeeded",
                "failed",
                "canceled",
                name="run_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=False,
        ),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_workflow_runs_brief_snapshot_id", "workflow_runs", ["brief_snapshot_id"])

    op.create_table(
        "workflow_step_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "workflow_run_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_runs.id"),
            nullable=False,
        ),
        sa.Column("step_name", sa.String(length=255), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "running",
                "paused",
                "succeeded",
                "failed",
                "canceled",
                name="step_status",
            ),
            nullable=False,
        ),
        sa.Column("outputs", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_workflow_step_runs_workflow_run_id", "workflow_step_runs", ["workflow_run_id"])

    op.create_table(
        "artifact_versions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "artifact_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id"),
            nullable=False,
        ),
        sa.Column("source", sa.Enum("user", "agent", name="artifact_version_source"), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "workflow_run_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_runs.id"),
            nullable=True,
        ),
        sa.Column(
            "brief_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brief_snapshots.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_artifact_versions_artifact_id", "artifact_versions", ["artifact_id"])
    op.create_index("ix_artifact_versions_workflow_run_id", "artifact_versions", ["workflow_run_id"])
    op.create_index("ix_artifact_versions_brief_snapshot_id", "artifact_versions", ["brief_snapshot_id"])


def downgrade() -> None:
    op.drop_index("ix_artifact_versions_brief_snapshot_id", table_name="artifact_versions")
    op.drop_index("ix_artifact_versions_workflow_run_id", table_name="artifact_versions")
    op.drop_index("ix_artifact_versions_artifact_id", table_name="artifact_versions")
    op.drop_table("artifact_versions")
    op.drop_table("workflow_step_runs")
    op.drop_table("workflow_runs")
    op.drop_table("artifacts")
    op.drop_index("ix_brief_snapshots_brief_id", table_name="brief_snapshots")
    op.drop_table("brief_snapshots")
    op.drop_table("briefs")

    op.execute("DROP EXTENSION IF EXISTS vector")
