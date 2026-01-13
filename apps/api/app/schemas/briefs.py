from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScriptFormat(str, enum.Enum):
    screenplay_int_ext = "screenplay_int_ext"
    stage_play = "stage_play"
    custom = "custom"


class OutputSpecResolved(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: str = Field(default="zh-CN")
    script_format: ScriptFormat = Field(default=ScriptFormat.screenplay_int_ext)
    script_format_notes: str | None = None
    max_fix_attempts: int = Field(default=2)


class OutputSpecOverrides(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: str | None = None
    script_format: ScriptFormat | None = None
    script_format_notes: str | None = None
    max_fix_attempts: int | None = None


class BriefContent(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str | None = None
    logline: str | None = None
    genres: list[str] = Field(default_factory=list)
    output_spec: OutputSpecOverrides = Field(default_factory=OutputSpecOverrides)


class BriefCreate(BaseModel):
    title: str | None = None
    content: BriefContent = Field(default_factory=BriefContent)


class BriefUpdate(BaseModel):
    title: str | None = None
    content: BriefContent | None = None


class BriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    content: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BriefSnapshotCreate(BaseModel):
    label: str | None = None


class BriefSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_id: uuid.UUID
    label: str | None
    content: dict[str, Any]
    created_at: datetime


class OutputSpecPatch(BaseModel):
    language: str | None = None
    script_format: ScriptFormat | None = None
    script_format_notes: str | None = None
    max_fix_attempts: int | None = None
