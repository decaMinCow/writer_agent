from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OpenThreadCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = Field(default="open")
    meta: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata", serialization_alias="metadata"
    )


class OpenThreadUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    meta: dict[str, Any] | None = Field(
        default=None, validation_alias="metadata", serialization_alias="metadata"
    )


class OpenThreadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    title: str
    description: str | None
    status: str
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime


class OpenThreadRefCreate(BaseModel):
    artifact_version_id: uuid.UUID
    ref_kind: str = Field(default="introduced")
    quote: str | None = None
    meta: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata", serialization_alias="metadata"
    )


class OpenThreadRefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    thread_id: uuid.UUID
    artifact_version_id: uuid.UUID
    ref_kind: str
    quote: str | None
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime

