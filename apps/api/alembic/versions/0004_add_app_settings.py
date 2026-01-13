"""add app settings

Revision ID: 0004_add_app_settings
Revises: 0003_add_memory_chunks
Create Date: 2026-01-12

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_add_app_settings"
down_revision = "0003_add_memory_chunks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_app_settings_updated_at", "app_settings", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_app_settings_updated_at", table_name="app_settings")
    op.drop_table("app_settings")

