from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ArtifactKind


class PropagationPreviewRequest(BaseModel):
    base_artifact_version_id: uuid.UUID
    edited_artifact_version_id: uuid.UUID


class ImpactReportItem(BaseModel):
    artifact_id: uuid.UUID
    artifact_version_id: uuid.UUID
    kind: ArtifactKind
    ordinal: int | None
    title: str | None
    reason: str


class PropagationPreviewResponse(BaseModel):
    fact_changes: str
    impacts: list[ImpactReportItem] = Field(default_factory=list)
    patches: dict[str, Any] = Field(default_factory=dict)


class PropagationApplyRequest(BaseModel):
    base_artifact_version_id: uuid.UUID
    edited_artifact_version_id: uuid.UUID


class PropagationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    base_artifact_version_id: uuid.UUID
    edited_artifact_version_id: uuid.UUID
    fact_changes: str
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime


class ArtifactImpactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    propagation_event_id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    artifact_id: uuid.UUID
    artifact_version_id: uuid.UUID
    reason: str
    repaired_artifact_version_id: uuid.UUID | None
    repaired_at: datetime | None
    created_at: datetime


class PropagationApplyResponse(BaseModel):
    event: PropagationEventRead
    impacts: list[ArtifactImpactRead] = Field(default_factory=list)


class PropagationRepairRequest(BaseModel):
    artifact_ids: list[uuid.UUID] | None = None


class RepairedArtifactVersion(BaseModel):
    artifact_id: uuid.UUID
    artifact_version_id: uuid.UUID


class PropagationRepairResponse(BaseModel):
    repaired: list[RepairedArtifactVersion] = Field(default_factory=list)
    impacts: list[ArtifactImpactRead] = Field(default_factory=list)

