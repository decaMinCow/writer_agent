from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class KgEntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    name: str
    entity_type: str
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime


class KgRelationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    subject_entity_id: uuid.UUID
    predicate: str
    object_entity_id: uuid.UUID
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime


class KgEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_snapshot_id: uuid.UUID
    event_key: str | None
    summary: str
    time_hint: str | None
    artifact_version_id: uuid.UUID | None
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime


class KnowledgeGraphRead(BaseModel):
    entities: list[KgEntityRead] = Field(default_factory=list)
    relations: list[KgRelationRead] = Field(default_factory=list)
    events: list[KgEventRead] = Field(default_factory=list)


class KnowledgeGraphRebuildResponse(BaseModel):
    entities_indexed: int
    relations_indexed: int
    events_indexed: int
