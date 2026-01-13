from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.workflows import WorkflowRunRead, WorkflowStepRunRead


class WorkflowInterventionRequest(BaseModel):
    instruction: str
    step_id: uuid.UUID | None = None


class WorkflowInterventionResult(BaseModel):
    assistant_message: str = Field(default="")
    state_patch: dict[str, Any] = Field(default_factory=dict)


class WorkflowInterventionResponse(BaseModel):
    run: WorkflowRunRead
    step: WorkflowStepRunRead
    assistant_message: str
    state_patch: dict[str, Any]

