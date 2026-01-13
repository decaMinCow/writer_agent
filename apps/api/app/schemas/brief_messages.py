from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import BriefMessageRole, WorkflowKind
from app.schemas.briefs import BriefRead


class BriefMessageCreate(BaseModel):
    content_text: str = Field(min_length=1)
    mode: WorkflowKind = Field(default=WorkflowKind.novel)


class BriefMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_id: uuid.UUID
    role: BriefMessageRole
    content_text: str
    meta: dict[str, Any] = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime


class GapReport(BaseModel):
    mode: WorkflowKind
    confirmed: list[str] = Field(default_factory=list)
    pending: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    conflict: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    completeness: int = Field(ge=0, le=100)


class BriefPatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str | None = None
    content: dict[str, Any] | None = None


class BriefBuilderResult(BaseModel):
    assistant_message: str = Field(default="")
    brief_patch: BriefPatch = Field(default_factory=BriefPatch)
    gap_report: GapReport


class BriefMessageCreateResponse(BaseModel):
    brief: BriefRead
    gap_report: GapReport
    messages: list[BriefMessageRead]
