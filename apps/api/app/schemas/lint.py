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

