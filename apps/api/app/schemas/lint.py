from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LintIssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    severity: str
    code: str
    message: str
    artifact_version_id: uuid.UUID | None
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime


class LintRunResponse(BaseModel):
    issues: list[LintIssueRead] = Field(default_factory=list)


class LintRepairRequest(BaseModel):
    max_targets: int = 10


class LintRepairResponse(BaseModel):
    repaired_count: int
    skipped_count: int
    repaired_artifact_version_ids: list[uuid.UUID] = Field(default_factory=list)
    created_artifact_version_ids: list[uuid.UUID] = Field(default_factory=list)
    skipped: list[dict[str, Any]] = Field(default_factory=list)
