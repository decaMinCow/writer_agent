from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import RunStatus, WorkflowKind
from app.schemas.briefs import OutputSpecOverrides


class WorkflowRunCreate(BaseModel):
    kind: WorkflowKind
    brief_snapshot_id: uuid.UUID
    source_brief_snapshot_id: uuid.UUID | None = None
    conversion_output_spec: OutputSpecOverrides | None = None
    prompt_preset_id: str | None = None
    status: RunStatus = Field(default=RunStatus.queued)
    state: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunPatch(BaseModel):
    status: RunStatus | None = None
    state: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class WorkflowRunForkRequest(BaseModel):
    step_id: uuid.UUID | None = None
    state: dict[str, Any] | None = None


class WorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: WorkflowKind
    status: RunStatus
    brief_snapshot_id: uuid.UUID
    state: dict[str, Any]
    error: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class WorkflowStepRunCreate(BaseModel):
    step_name: str
    step_index: int | None = None
    status: RunStatus = Field(default=RunStatus.queued)
    outputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowStepRunPatch(BaseModel):
    status: RunStatus | None = None
    outputs: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class WorkflowStepRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_run_id: uuid.UUID
    step_name: str
    step_index: int | None
    status: RunStatus
    outputs: dict[str, Any]
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
