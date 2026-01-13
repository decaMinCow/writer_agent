from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GlossaryEntryCreate(BaseModel):
    term: str
    replacement: str
    meta: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata", serialization_alias="metadata"
    )


class GlossaryEntryUpdate(BaseModel):
    term: str | None = None
    replacement: str | None = None
    meta: dict[str, Any] | None = Field(
        default=None, validation_alias="metadata", serialization_alias="metadata"
    )


class GlossaryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    term: str
    replacement: str
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime


class ExportResponse(BaseModel):
    filename: str
    content_type: str
    text: str

