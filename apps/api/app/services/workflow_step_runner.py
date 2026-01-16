from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RunStatus, WorkflowKind, WorkflowRun, WorkflowStepRun
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.schemas.workflows import WorkflowRunRead, WorkflowStepRunRead
from app.services.error_utils import format_exception_chain
from app.services.workflow_events import WorkflowEventHub
from app.services.workflow_executor import execute_next_step


def _now() -> datetime:
    return datetime.now().astimezone()


def determine_step_name(run: WorkflowRun) -> str:
    cursor = (run.state or {}).get("cursor") if isinstance(run.state, dict) else None
    phase = cursor.get("phase") if isinstance(cursor, dict) else None
    if phase:
        return str(phase)
    if run.kind == WorkflowKind.novel:
        return "novel_outline"
    if run.kind == WorkflowKind.script:
        return "script_scene_list"
    if run.kind == WorkflowKind.novel_to_script:
        state = run.state or {}
        split_mode = state.get("split_mode") if isinstance(state, dict) else None
        if split_mode == "auto_by_length":
            return "nts_chapter_plan"
        return "nts_episode_breakdown"
    return "start"


async def _publish_run(hub: WorkflowEventHub | None, *, run: WorkflowRun) -> None:
    if hub is None:
        return
    await hub.publish(
        run_id=run.id,
        name="run",
        payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
    )


async def _publish_step(hub: WorkflowEventHub | None, *, step: WorkflowStepRun) -> None:
    if hub is None:
        return
    await hub.publish(
        run_id=step.workflow_run_id,
        name="step",
        payload={"step": WorkflowStepRunRead.model_validate(step).model_dump(mode="json")},
    )


async def execute_one_step(
    *,
    session: AsyncSession,
    llm: LLMClient,
    embeddings: EmbeddingsClient,
    run: WorkflowRun,
    hub: WorkflowEventHub | None = None,
) -> WorkflowStepRun:
    if run.status == RunStatus.paused:
        raise RuntimeError("workflow_run_paused")
    if run.status in {RunStatus.succeeded, RunStatus.failed, RunStatus.canceled}:
        raise RuntimeError("workflow_run_not_runnable")

    if run.status == RunStatus.queued:
        run.status = RunStatus.running
        await session.commit()
        await session.refresh(run)
        await _publish_run(hub, run=run)

    step_name = determine_step_name(run)

    next_index = await session.scalar(
        select(func.count()).select_from(WorkflowStepRun).where(WorkflowStepRun.workflow_run_id == run.id)
    )
    step_index = int(next_index or 0) + 1

    step = WorkflowStepRun(
        workflow_run_id=run.id,
        step_name=step_name,
        step_index=step_index,
        status=RunStatus.running,
        outputs={},
        started_at=_now(),
    )
    session.add(step)
    await session.commit()
    await session.refresh(step)
    await _publish_step(hub, step=step)

    try:
        outputs: dict[str, Any] = await execute_next_step(
            session=session, llm=llm, embeddings=embeddings, run=run, hub=hub, step_id=step.id
        )
        if run.status == RunStatus.failed:
            step.status = RunStatus.failed
            if run.error:
                step.error = json.dumps(run.error, ensure_ascii=False)
        else:
            step.status = RunStatus.succeeded
        step.outputs = outputs
        step.finished_at = _now()
        await session.commit()
        await session.refresh(step)
        await session.refresh(run)
        await _publish_step(hub, step=step)
        await _publish_run(hub, run=run)
        return step
    except Exception as exc:
        error_chain = format_exception_chain(exc)
        step.status = RunStatus.failed
        step.error = error_chain
        step.finished_at = _now()
        run.status = RunStatus.failed
        run.error = {
            "detail": "step_failed",
            "step_name": step_name,
            "step_index": step_index,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
            "error_chain": error_chain,
        }
        await session.commit()
        await session.refresh(step)
        await session.refresh(run)
        await _publish_step(hub, step=step)
        await _publish_run(hub, run=run)
        return step
