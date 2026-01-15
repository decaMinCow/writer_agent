from __future__ import annotations

import asyncio
import copy
import json
import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.db.models import BriefSnapshot, RunStatus, WorkflowKind, WorkflowRun, WorkflowStepRun
from app.db.session import get_db_session
from app.schemas.workflow_execution import WorkflowControlResponse, WorkflowNextResponse
from app.schemas.workflow_interventions import (
    WorkflowInterventionRequest,
    WorkflowInterventionResponse,
)
from app.schemas.workflows import (
    WorkflowRunCreate,
    WorkflowRunForkRequest,
    WorkflowRunPatch,
    WorkflowRunRead,
    WorkflowStepRunCreate,
    WorkflowStepRunPatch,
    WorkflowStepRunRead,
)
from app.services import cascade_delete
from app.services.error_utils import format_exception_chain
from app.services.json_utils import deep_merge
from app.services.llm_provider import resolve_llm_and_embeddings, resolve_llm_client
from app.services.workflow_events import WorkflowEventHub, format_sse_event
from app.services.workflow_executor import execute_next_step
from app.services.workflow_intervention import build_workflow_intervention
from app.services.workflow_step_runner import determine_step_name, execute_one_step

router = APIRouter(prefix="/api/workflow-runs", tags=["workflows"])

_ERROR_CODE_RE = re.compile(r"Error code:\s*(\d+)")


def _reset_failed_cursor_phase(state: dict[str, Any]) -> dict[str, Any]:
    cursor = state.get("cursor")
    if not isinstance(cursor, dict):
        return state
    if cursor.get("phase") != "failed":
        return state
    next_cursor = dict(cursor)
    next_cursor.pop("phase", None)
    next_state = dict(state)
    next_state["cursor"] = next_cursor
    return next_state


def _output_spec_from_snapshot(snapshot: BriefSnapshot | None) -> dict[str, Any]:
    if snapshot is None:
        return {}
    content = snapshot.content
    if not isinstance(content, dict):
        return {}
    output_spec = content.get("output_spec")
    if not isinstance(output_spec, dict):
        return {}
    return dict(output_spec)


def _coerce_int(value: object, *, default: int, min_value: int = 0) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        parsed = default
    return max(min_value, parsed)


def _coerce_float(value: object, *, default: float, min_value: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        parsed = default
    return max(min_value, parsed)


def _resolve_autorun_retry_policy(*, snapshot: BriefSnapshot | None) -> tuple[int, float]:
    output_spec = _output_spec_from_snapshot(snapshot)
    retries = _coerce_int(output_spec.get("auto_step_retries"), default=3, min_value=0)
    backoff_s = _coerce_float(output_spec.get("auto_step_backoff_s"), default=1.0, min_value=0.0)
    return retries, backoff_s


def _is_retryable_step_failure(*, run_error: dict[str, Any] | None, step_error: str | None) -> bool:
    if not isinstance(run_error, dict):
        return False

    detail = str(run_error.get("detail") or "")
    if detail in {"hard_check_failed", "max_fix_attempts_exceeded"}:
        return False

    error_type = str(run_error.get("error_type") or "")
    if error_type in {"APIConnectionError", "APITimeoutError"}:
        return True
    if error_type in {"JSONDecodeError", "ValidationError"}:
        return True
    if error_type == "ValueError":
        msg = str(run_error.get("error") or "")
        if "expected_json_object" in msg:
            return True

    chain = str(run_error.get("error_chain") or step_error or "")
    if "SSLEOFError" in chain or "UNEXPECTED_EOF_WHILE_READING" in chain:
        return True
    if "RemoteProtocolError" in chain or "EndOfStream" in chain:
        return True

    if error_type == "APIStatusError" or "APIStatusError" in chain:
        match = _ERROR_CODE_RE.search(chain) or _ERROR_CODE_RE.search(str(run_error.get("error") or ""))
        if match:
            try:
                code = int(match.group(1))
            except ValueError:
                code = 0
            if code in {408, 409, 429, 500, 502, 503, 504}:
                return True

    return False


def _autorun_retry_state(state: dict[str, Any]) -> dict[str, Any]:
    blob = state.get("_autorun_retry")
    if isinstance(blob, dict):
        return blob
    blob = {}
    state["_autorun_retry"] = blob
    return blob


def _compute_backoff_delay_s(*, base_backoff_s: float, attempt: int, cap_s: float = 30.0) -> float:
    if base_backoff_s <= 0:
        return 0.0
    if attempt <= 1:
        return min(cap_s, base_backoff_s)
    return min(cap_s, base_backoff_s * (2 ** (attempt - 1)))


@router.post("", response_model=WorkflowRunRead)
async def create_workflow_run(
    payload: WorkflowRunCreate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowRunRead:
    snapshot = await session.get(BriefSnapshot, payload.brief_snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="brief_snapshot_not_found")

    state: dict[str, Any] = dict(payload.state or {})
    prompt_preset_id = (payload.prompt_preset_id or "").strip() or None

    if payload.kind == WorkflowKind.novel_to_script:
        if payload.source_brief_snapshot_id is not None:
            source = await session.get(BriefSnapshot, payload.source_brief_snapshot_id)
            if not source:
                raise HTTPException(status_code=404, detail="source_snapshot_not_found")
            if source.brief_id != snapshot.brief_id:
                raise HTTPException(status_code=400, detail="source_snapshot_not_in_same_brief")
            state["novel_source_snapshot_id"] = str(source.id)

        if payload.conversion_output_spec is not None:
            overrides = payload.conversion_output_spec.model_dump(mode="json", exclude_none=True)
            if overrides:
                state["conversion_output_spec"] = overrides
        if prompt_preset_id is not None:
            state["prompt_preset_id"] = prompt_preset_id

    elif payload.kind == WorkflowKind.script:
        if payload.source_brief_snapshot_id is not None or payload.conversion_output_spec is not None:
            raise HTTPException(status_code=400, detail="unsupported_workflow_inputs")
        if prompt_preset_id is not None:
            state["prompt_preset_id"] = prompt_preset_id

    else:
        if (
            payload.source_brief_snapshot_id is not None
            or payload.conversion_output_spec is not None
            or payload.prompt_preset_id is not None
        ):
            raise HTTPException(status_code=400, detail="unsupported_workflow_inputs")

    run = WorkflowRun(
        kind=payload.kind,
        status=payload.status,
        brief_snapshot_id=snapshot.id,
        state=state,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return WorkflowRunRead.model_validate(run)


@router.get("", response_model=list[WorkflowRunRead])
async def list_workflow_runs(
    brief_snapshot_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[WorkflowRunRead]:
    stmt = select(WorkflowRun)
    if brief_snapshot_id is not None:
        stmt = stmt.where(WorkflowRun.brief_snapshot_id == brief_snapshot_id)
    stmt = stmt.order_by(WorkflowRun.updated_at.desc())
    result = await session.execute(stmt)
    items = result.scalars().all()
    return [WorkflowRunRead.model_validate(item) for item in items]


@router.delete("/{run_id}")
async def delete_workflow_run(
    run_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    await cascade_delete.delete_workflow_run(session=session, run_id=run.id, app=request.app)
    return {"deleted": True}


@router.post("/{run_id}/interventions", response_model=WorkflowInterventionResponse)
async def apply_workflow_intervention(
    run_id: uuid.UUID,
    payload: WorkflowInterventionRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowInterventionResponse:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")
    if run.status in {RunStatus.succeeded, RunStatus.canceled}:
        raise HTTPException(status_code=400, detail="workflow_run_not_intervenable")

    target_step: WorkflowStepRun | None = None
    if payload.step_id is not None:
        target_step = await session.get(WorkflowStepRun, payload.step_id)
        if not target_step:
            raise HTTPException(status_code=404, detail="workflow_step_run_not_found")
        if target_step.workflow_run_id != run.id:
            raise HTTPException(status_code=400, detail="workflow_step_not_in_run")

    llm = await resolve_llm_client(session=session, app=request.app)
    if llm is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    instruction = (payload.instruction or "").strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="instruction_required")

    run_state: dict[str, Any] = dict(run.state or {})
    target_step_json: dict[str, Any] | None = None
    if target_step is not None:
        target_step_json = {
            "id": str(target_step.id),
            "step_name": target_step.step_name,
            "step_index": target_step.step_index,
            "status": str(target_step.status.value),
            "outputs": dict(target_step.outputs or {}),
            "error": target_step.error,
        }

    result = await build_workflow_intervention(
        llm=llm,
        run_kind=str(run.kind.value),
        run_status=str(run.status.value),
        run_state=run_state,
        instruction=instruction,
        target_step=target_step_json,
    )

    patch = dict(result.state_patch or {})
    run.state = deep_merge(run_state, patch)

    # Record as a step run for audit/history.
    next_index = await session.scalar(
        select(func.count()).select_from(WorkflowStepRun).where(WorkflowStepRun.workflow_run_id == run.id)
    )
    step_index = int(next_index or 0) + 1
    now = datetime.now().astimezone()
    step = WorkflowStepRun(
        workflow_run_id=run.id,
        step_name="intervention",
        step_index=step_index,
        status=RunStatus.succeeded,
        outputs={
            "instruction": instruction,
            "assistant_message": result.assistant_message,
            "state_patch": patch,
            "target_step_id": str(target_step.id) if target_step is not None else None,
            "target_step_name": target_step.step_name if target_step is not None else None,
        },
        error=None,
        started_at=now,
        finished_at=now,
    )
    session.add(step)
    await session.commit()
    await session.refresh(step)
    await session.refresh(run)

    hub = getattr(request.app.state, "workflow_event_hub", None)
    if hub is not None:
        await hub.publish(
            run_id=run.id,
            name="step",
            payload={"step": WorkflowStepRunRead.model_validate(step).model_dump(mode="json")},
        )
        await hub.publish(
            run_id=run.id,
            name="run",
            payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
        )

    return WorkflowInterventionResponse(
        run=WorkflowRunRead.model_validate(run),
        step=WorkflowStepRunRead.model_validate(step),
        assistant_message=result.assistant_message,
        state_patch=patch,
    )


@router.get("/{run_id}", response_model=WorkflowRunRead)
async def get_workflow_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowRunRead:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")
    return WorkflowRunRead.model_validate(run)


@router.post("/{run_id}/fork", response_model=WorkflowRunRead)
async def fork_workflow_run(
    run_id: uuid.UUID,
    payload: WorkflowRunForkRequest,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowRunRead:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    if payload.step_id is not None:
        step = await session.get(WorkflowStepRun, payload.step_id)
        if not step:
            raise HTTPException(status_code=404, detail="workflow_step_run_not_found")
        if step.workflow_run_id != run.id:
            raise HTTPException(status_code=400, detail="workflow_step_not_in_run")

    state: dict[str, Any] = dict(payload.state if payload.state is not None else (run.state or {}))
    state["forked_from"] = {"run_id": str(run.id), "step_id": str(payload.step_id) if payload.step_id else None}
    state = _reset_failed_cursor_phase(state)

    forked = WorkflowRun(
        kind=run.kind,
        status=RunStatus.queued,
        brief_snapshot_id=run.brief_snapshot_id,
        state=state,
        error=None,
    )
    session.add(forked)
    await session.commit()
    await session.refresh(forked)
    return WorkflowRunRead.model_validate(forked)


@router.get("/{run_id}/events")
async def workflow_run_events(
    run_id: uuid.UUID,
    request: Request,
    once: bool = False,
) -> StreamingResponse:
    # NOTE: Do not keep a DB session open for the lifetime of an SSE connection.
    sessionmaker = getattr(request.app.state, "sessionmaker", None)
    if sessionmaker is None:
        raise HTTPException(status_code=500, detail="db_not_initialized")

    async with sessionmaker() as session:
        run = await session.get(WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="workflow_run_not_found")

    hub = getattr(request.app.state, "workflow_event_hub", None)
    if hub is None:
        hub = WorkflowEventHub()
        request.app.state.workflow_event_hub = hub

    queue = await hub.subscribe(run_id=run.id)
    initial = {"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")}

    async def event_stream():
        try:
            yield format_sse_event(name="run", payload=initial)
            if once:
                return
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield format_sse_event(name=event.name, payload=event.payload)
        finally:
            await hub.unsubscribe(run_id=run.id, queue=queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"cache-control": "no-cache"},
    )


@router.patch("/{run_id}", response_model=WorkflowRunRead)
async def patch_workflow_run(
    run_id: uuid.UUID,
    payload: WorkflowRunPatch,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowRunRead:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    if payload.status is not None:
        run.status = payload.status
    if payload.state is not None:
        run.state = payload.state
    if payload.error is not None:
        run.error = payload.error

    await session.commit()
    await session.refresh(run)
    return WorkflowRunRead.model_validate(run)


@router.post("/{run_id}/steps", response_model=WorkflowStepRunRead)
async def create_step_run(
    run_id: uuid.UUID,
    payload: WorkflowStepRunCreate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowStepRunRead:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    step = WorkflowStepRun(
        workflow_run_id=run.id,
        step_name=payload.step_name,
        step_index=payload.step_index,
        status=payload.status,
        outputs=payload.outputs,
        started_at=datetime.now().astimezone(),
    )
    session.add(step)
    await session.commit()
    await session.refresh(step)
    return WorkflowStepRunRead.model_validate(step)


@router.get("/{run_id}/steps", response_model=list[WorkflowStepRunRead])
async def list_step_runs(
    run_id: uuid.UUID,
    limit: int = 200,
    session: AsyncSession = Depends(get_db_session),
) -> list[WorkflowStepRunRead]:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    # Some runs can accumulate a very large number of step rows (e.g. long autoruns).
    # Returning every step can freeze the API/UI. Default to the latest N steps.
    limit = _coerce_int(limit, default=200, min_value=1)
    limit = min(limit, 2000)

    result = await session.execute(
        select(WorkflowStepRun)
        .where(WorkflowStepRun.workflow_run_id == run.id)
        .order_by(WorkflowStepRun.step_index.desc().nullslast(), WorkflowStepRun.created_at.desc())
        .limit(limit)
    )
    items = list(result.scalars().all())
    items.reverse()
    return [WorkflowStepRunRead.model_validate(item) for item in items]


@router.patch("/steps/{step_id}", response_model=WorkflowStepRunRead)
async def patch_step_run(
    step_id: uuid.UUID,
    payload: WorkflowStepRunPatch,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowStepRunRead:
    step = await session.get(WorkflowStepRun, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="workflow_step_run_not_found")

    if payload.status is not None:
        step.status = payload.status
    if payload.outputs is not None:
        step.outputs = payload.outputs
    if payload.error is not None:
        step.error = payload.error
    if payload.started_at is not None:
        step.started_at = payload.started_at
    if payload.finished_at is not None:
        step.finished_at = payload.finished_at

    await session.commit()
    await session.refresh(step)
    return WorkflowStepRunRead.model_validate(step)


@router.post("/{run_id}/pause", response_model=WorkflowControlResponse)
async def pause_workflow_run(
    run_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowControlResponse:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")
    if run.status in {RunStatus.succeeded, RunStatus.failed, RunStatus.canceled}:
        raise HTTPException(status_code=400, detail="workflow_run_not_pauseable")

    run.status = RunStatus.paused
    await session.commit()
    await session.refresh(run)
    hub = getattr(request.app.state, "workflow_event_hub", None)
    if hub is not None:
        await hub.publish(
            run_id=run.id,
            name="run",
            payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
        )
    return WorkflowControlResponse(run=WorkflowRunRead.model_validate(run))


@router.post("/{run_id}/resume", response_model=WorkflowControlResponse)
async def resume_workflow_run(
    run_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowControlResponse:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")
    if run.status != RunStatus.paused:
        raise HTTPException(status_code=400, detail="workflow_run_not_paused")

    run.status = RunStatus.running
    await session.commit()
    await session.refresh(run)
    hub = getattr(request.app.state, "workflow_event_hub", None)
    if hub is not None:
        await hub.publish(
            run_id=run.id,
            name="run",
            payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
        )
    return WorkflowControlResponse(run=WorkflowRunRead.model_validate(run))


@router.post("/{run_id}/next", response_model=WorkflowNextResponse)
async def execute_workflow_next(
    run_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowNextResponse:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    if run.status == RunStatus.paused:
        raise HTTPException(status_code=400, detail="workflow_run_paused")
    if run.status in {RunStatus.succeeded, RunStatus.canceled}:
        raise HTTPException(status_code=400, detail="workflow_run_not_runnable")

    if run.status == RunStatus.failed:
        run.status = RunStatus.queued
        run.error = None
        run.state = _reset_failed_cursor_phase(dict(run.state or {}))
        await session.commit()
        await session.refresh(run)

    llm, embeddings, meta = await resolve_llm_and_embeddings(session=session, app=request.app)
    if llm is None or embeddings is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    hub = getattr(request.app.state, "workflow_event_hub", None)
    step = await execute_one_step(session=session, llm=llm, embeddings=embeddings, run=run, hub=hub)
    await session.refresh(run)

    if run.status == RunStatus.failed and isinstance(run.error, dict):
        effective = meta.get("effective")
        if isinstance(effective, dict):
            run.error = deep_merge(dict(run.error), {"provider": effective})
            await session.commit()
            await session.refresh(run)
            if hub is not None:
                await hub.publish(
                    run_id=run.id,
                    name="run",
                    payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
                )

    return WorkflowNextResponse(
        run=WorkflowRunRead.model_validate(run),
        step=WorkflowStepRunRead.model_validate(step),
    )


async def _autorun_loop(app: FastAPI, *, run_id: uuid.UUID, stop_event: asyncio.Event) -> None:
    sessionmaker = getattr(app.state, "sessionmaker", None)
    hub = getattr(app.state, "workflow_event_hub", None)

    if sessionmaker is None:
        return

    try:
        while not stop_event.is_set():
            retry_delay_s: float | None = None
            async with sessionmaker() as session:
                run = await session.get(WorkflowRun, run_id)
                if not run:
                    return
                if run.status == RunStatus.paused:
                    return
                if run.status in {RunStatus.succeeded, RunStatus.failed, RunStatus.canceled}:
                    return

                snapshot = await session.get(BriefSnapshot, run.brief_snapshot_id)
                max_step_retries, backoff_s = _resolve_autorun_retry_policy(snapshot=snapshot)

                llm, embeddings, meta = await resolve_llm_and_embeddings(session=session, app=app)
                if llm is None or embeddings is None:
                    return

                if run.status == RunStatus.queued:
                    run.status = RunStatus.running
                    await session.commit()
                    await session.refresh(run)
                    if hub is not None:
                        await hub.publish(
                            run_id=run.id,
                            name="run",
                            payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
                        )

                step_name = str(determine_step_name(run))
                next_index = await session.scalar(
                    select(func.count())
                    .select_from(WorkflowStepRun)
                    .where(WorkflowStepRun.workflow_run_id == run.id)
                )
                step_index = int(next_index or 0) + 1
                now = datetime.now().astimezone()
                step = WorkflowStepRun(
                    workflow_run_id=run.id,
                    step_name=step_name,
                    step_index=step_index,
                    status=RunStatus.running,
                    outputs={},
                    started_at=now,
                )
                session.add(step)
                await session.commit()
                await session.refresh(step)
                if hub is not None:
                    await hub.publish(
                        run_id=run.id,
                        name="step",
                        payload={"step": WorkflowStepRunRead.model_validate(step).model_dump(mode="json")},
                    )

                run_error: dict[str, Any] | None = None
                try:
                    outputs = await execute_next_step(
                        session=session,
                        llm=llm,
                        embeddings=embeddings,
                        run=run,
                        hub=hub,
                        step_id=step.id,
                    )
                    step.outputs = outputs
                    step.finished_at = datetime.now().astimezone()

                    if run.status == RunStatus.failed:
                        run_error = run.error if isinstance(run.error, dict) else None
                        step.status = RunStatus.failed
                        if run_error is not None:
                            step.error = json.dumps(run_error, ensure_ascii=False)
                    else:
                        step.status = RunStatus.succeeded
                except Exception as exc:
                    step.finished_at = datetime.now().astimezone()
                    step.status = RunStatus.failed
                    step.outputs = {}
                    step.error = format_exception_chain(exc)
                    run_error = {
                        "detail": "step_failed",
                        "step_name": step_name,
                        "step_index": step_index,
                        "error_type": exc.__class__.__name__,
                        "error": str(exc),
                        "error_chain": step.error,
                    }

                if step.status == RunStatus.failed and run_error is not None:
                    state: dict[str, Any] = copy.deepcopy(run.state or {})
                    retry_state = _autorun_retry_state(state)
                    prev_step_name = str(retry_state.get("step_name") or "")
                    if prev_step_name != step_name:
                        retry_state.clear()
                        retry_state["step_name"] = step_name
                        retry_state["attempt"] = 0

                    attempt = int(retry_state.get("attempt") or 0) + 1
                    retry_state["attempt"] = attempt

                    retryable = _is_retryable_step_failure(run_error=run_error, step_error=step.error)

                    if retryable and attempt <= max_step_retries:
                        retry_delay_s = _compute_backoff_delay_s(base_backoff_s=backoff_s, attempt=attempt)
                        run.status = RunStatus.queued
                        run.error = None
                        run.state = state

                        await session.commit()
                        await session.refresh(run)
                        await session.refresh(step)

                        if hub is not None:
                            await hub.publish(
                                run_id=run.id,
                                name="step",
                                payload={
                                    "step": WorkflowStepRunRead.model_validate(step).model_dump(mode="json")
                                },
                            )
                            await hub.publish(
                                run_id=run.id,
                                name="run",
                                payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
                            )
                            await hub.publish(
                                run_id=run.id,
                                name="log",
                                payload={
                                    "message": f"autorun_retry_scheduled step={step_name} attempt={attempt}/{max_step_retries} delay_s={retry_delay_s}"
                                },
                            )
                        continue

                    run.status = RunStatus.failed
                    effective = meta.get("effective")
                    if isinstance(effective, dict):
                        run_error = deep_merge(dict(run_error), {"provider": effective})
                    if retryable and attempt > max_step_retries:
                        run_error = deep_merge(
                            dict(run_error),
                            {
                                "autorun_retry_exhausted": True,
                                "autorun_retry_attempts": attempt,
                                "autorun_retry_limit": max_step_retries,
                            },
                        )

                    run.error = run_error
                    run.state = state
                    await session.commit()
                    await session.refresh(run)
                    await session.refresh(step)

                    if hub is not None:
                        await hub.publish(
                            run_id=run.id,
                            name="step",
                            payload={"step": WorkflowStepRunRead.model_validate(step).model_dump(mode="json")},
                        )
                        await hub.publish(
                            run_id=run.id,
                            name="run",
                            payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
                        )
                        reason = "not_retryable" if not retryable else "retry_limit_exhausted"
                        await hub.publish(
                            run_id=run.id,
                            name="log",
                            payload={
                                "message": f"autorun_stopped_on_failure step={step_name} attempt={attempt}/{max_step_retries} reason={reason}"
                            },
                        )
                    return

                if step.status == RunStatus.failed and run_error is None:
                    run.status = RunStatus.failed
                    run.error = {"detail": "step_failed", "step_name": step_name, "step_index": step_index}
                    await session.commit()
                    await session.refresh(run)
                    await session.refresh(step)
                    if hub is not None:
                        await hub.publish(
                            run_id=run.id,
                            name="step",
                            payload={"step": WorkflowStepRunRead.model_validate(step).model_dump(mode="json")},
                        )
                        await hub.publish(
                            run_id=run.id,
                            name="run",
                            payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
                        )
                    return

                state: dict[str, Any] = copy.deepcopy(run.state or {})
                if "_autorun_retry" in state:
                    state.pop("_autorun_retry", None)
                    run.state = state
                await session.commit()
                await session.refresh(run)
                await session.refresh(step)
                if hub is not None:
                    await hub.publish(
                        run_id=run.id,
                        name="step",
                        payload={"step": WorkflowStepRunRead.model_validate(step).model_dump(mode="json")},
                    )
                    await hub.publish(
                        run_id=run.id,
                        name="run",
                        payload={"run": WorkflowRunRead.model_validate(run).model_dump(mode="json")},
                    )

            if retry_delay_s is None:
                await asyncio.sleep(0)
            elif retry_delay_s <= 0:
                await asyncio.sleep(0)
            else:
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=retry_delay_s)
                except asyncio.TimeoutError:
                    pass
    except asyncio.CancelledError:
        return
    except Exception as exc:
        if hub is not None:
            await hub.publish(run_id=run_id, name="log", payload={"message": str(exc)})
    finally:
        tasks = getattr(app.state, "workflow_autorun_tasks", None)
        flags = getattr(app.state, "workflow_autorun_stop_flags", None)
        if isinstance(tasks, dict):
            tasks.pop(run_id, None)
        if isinstance(flags, dict):
            flags.pop(run_id, None)
        if hub is not None:
            await hub.publish(run_id=run_id, name="log", payload={"message": "autorun_stopped"})


@router.post("/{run_id}/autorun/start", response_model=WorkflowControlResponse)
async def autorun_start(
    run_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowControlResponse:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")
    if run.status == RunStatus.paused:
        raise HTTPException(status_code=400, detail="workflow_run_paused")
    if run.status in {RunStatus.succeeded, RunStatus.canceled}:
        raise HTTPException(status_code=400, detail="workflow_run_not_runnable")

    if run.status == RunStatus.failed:
        run.status = RunStatus.queued
        run.error = None
        run.state = _reset_failed_cursor_phase(dict(run.state or {}))
        await session.commit()
        await session.refresh(run)

    llm, embeddings, _meta = await resolve_llm_and_embeddings(session=session, app=request.app)
    if llm is None or embeddings is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    tasks = getattr(request.app.state, "workflow_autorun_tasks", None)
    flags = getattr(request.app.state, "workflow_autorun_stop_flags", None)
    if not isinstance(tasks, dict) or not isinstance(flags, dict):
        raise HTTPException(status_code=500, detail="autorun_not_initialized")

    existing = tasks.get(run.id)
    if existing is not None and not existing.done():
        return WorkflowControlResponse(run=WorkflowRunRead.model_validate(run))

    stop_event = asyncio.Event()
    flags[run.id] = stop_event
    tasks[run.id] = asyncio.create_task(_autorun_loop(request.app, run_id=run.id, stop_event=stop_event))

    hub = getattr(request.app.state, "workflow_event_hub", None)
    if hub is not None:
        await hub.publish(run_id=run.id, name="log", payload={"message": "autorun_started"})

    return WorkflowControlResponse(run=WorkflowRunRead.model_validate(run))


@router.post("/{run_id}/autorun/stop", response_model=WorkflowControlResponse)
async def autorun_stop(
    run_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowControlResponse:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    tasks = getattr(request.app.state, "workflow_autorun_tasks", None)
    flags = getattr(request.app.state, "workflow_autorun_stop_flags", None)
    if isinstance(flags, dict):
        stop_event = flags.get(run.id)
        if isinstance(stop_event, asyncio.Event):
            stop_event.set()

    if isinstance(tasks, dict):
        task = tasks.get(run.id)
        if task is not None and getattr(task, "done", lambda: False)():
            tasks.pop(run.id, None)

    hub = getattr(request.app.state, "workflow_event_hub", None)
    if hub is not None:
        await hub.publish(run_id=run.id, name="log", payload={"message": "autorun_stop_requested"})

    return WorkflowControlResponse(run=WorkflowRunRead.model_validate(run))
