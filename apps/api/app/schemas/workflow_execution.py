from __future__ import annotations

from pydantic import BaseModel

from app.schemas.workflows import WorkflowRunRead, WorkflowStepRunRead


class WorkflowNextResponse(BaseModel):
    run: WorkflowRunRead
    step: WorkflowStepRunRead


class WorkflowControlResponse(BaseModel):
    run: WorkflowRunRead

