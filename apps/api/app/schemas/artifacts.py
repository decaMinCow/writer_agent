from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ArtifactKind, ArtifactVersionSource


class ArtifactCreate(BaseModel):
    kind: ArtifactKind
    title: str | None = None
    ordinal: int | None = None


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: ArtifactKind
    title: str | None
    ordinal: int | None
    created_at: datetime
    updated_at: datetime


class ArtifactVersionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: ArtifactVersionSource = Field(default=ArtifactVersionSource.agent)
    content_text: str
    meta: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata", serialization_alias="metadata"
    )
    workflow_run_id: uuid.UUID | None = None
    brief_snapshot_id: uuid.UUID | None = None


class ArtifactVersionRewriteRequest(BaseModel):
    instruction: str
    selection_start: int | None = None
    selection_end: int | None = None


class ArtifactVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_id: uuid.UUID
    source: ArtifactVersionSource
    content_text: str
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    workflow_run_id: uuid.UUID | None
    brief_snapshot_id: uuid.UUID | None
    created_at: datetime
