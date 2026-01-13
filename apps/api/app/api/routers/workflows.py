from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.db.models import BriefSnapshot, RunStatus, WorkflowRun, WorkflowStepRun
from app.db.session import get_db_session
from app.schemas.workflow_execution import WorkflowControlResponse, WorkflowNextResponse
from app.schemas.workflows import (
    WorkflowRunCreate,
    WorkflowRunForkRequest,
    WorkflowRunPatch,
    WorkflowRunRead,
    WorkflowStepRunCreate,
    WorkflowStepRunPatch,
    WorkflowStepRunRead,
)
from app.services.workflow_events import WorkflowEventHub, format_sse_event
from app.services.workflow_step_runner import execute_one_step

router = APIRouter(prefix="/api/workflow-runs", tags=["workflows"])


@router.post("", response_model=WorkflowRunRead)
async def create_workflow_run(
    payload: WorkflowRunCreate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowRunRead:
    snapshot = await session.get(BriefSnapshot, payload.brief_snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="brief_snapshot_not_found")

    run = WorkflowRun(
        kind=payload.kind,
        status=payload.status,
        brief_snapshot_id=snapshot.id,
        state=payload.state,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return WorkflowRunRead.model_validate(run)


@router.get("", response_model=list[WorkflowRunRead])
async def list_workflow_runs(session: AsyncSession = Depends(get_db_session)) -> list[WorkflowRunRead]:
    result = await session.execute(select(WorkflowRun).order_by(WorkflowRun.updated_at.desc()))
    items = result.scalars().all()
    return [WorkflowRunRead.model_validate(item) for item in items]


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
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
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
    session: AsyncSession = Depends(get_db_session),
) -> list[WorkflowStepRunRead]:
    run = await session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")

    result = await session.execute(
        select(WorkflowStepRun)
        .where(WorkflowStepRun.workflow_run_id == run.id)
        .order_by(WorkflowStepRun.step_index.asc().nullslast(), WorkflowStepRun.created_at.asc())
    )
    items = result.scalars().all()
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
    if run.status in {RunStatus.succeeded, RunStatus.failed, RunStatus.canceled}:
        raise HTTPException(status_code=400, detail="workflow_run_not_runnable")

    llm = getattr(request.app.state, "llm_client", None)
    embeddings = getattr(request.app.state, "embeddings_client", None)
    if llm is None or embeddings is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    hub = getattr(request.app.state, "workflow_event_hub", None)
    step = await execute_one_step(session=session, llm=llm, embeddings=embeddings, run=run, hub=hub)
    await session.refresh(run)
    return WorkflowNextResponse(
        run=WorkflowRunRead.model_validate(run),
        step=WorkflowStepRunRead.model_validate(step),
    )


async def _autorun_loop(app: FastAPI, *, run_id: uuid.UUID, stop_event: asyncio.Event) -> None:
    sessionmaker = getattr(app.state, "sessionmaker", None)
    hub = getattr(app.state, "workflow_event_hub", None)
    llm = getattr(app.state, "llm_client", None)
    embeddings = getattr(app.state, "embeddings_client", None)

    if sessionmaker is None or llm is None or embeddings is None:
        return

    try:
        while not stop_event.is_set():
            async with sessionmaker() as session:
                run = await session.get(WorkflowRun, run_id)
                if not run:
                    return
                if run.status == RunStatus.paused:
                    return
                if run.status in {RunStatus.succeeded, RunStatus.failed, RunStatus.canceled}:
                    return
                await execute_one_step(
                    session=session,
                    llm=llm,
                    embeddings=embeddings,
                    run=run,
                    hub=hub,
                )
            await asyncio.sleep(0)
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
    if run.status in {RunStatus.succeeded, RunStatus.failed, RunStatus.canceled}:
        raise HTTPException(status_code=400, detail="workflow_run_not_runnable")

    llm = getattr(request.app.state, "llm_client", None)
    embeddings = getattr(request.app.state, "embeddings_client", None)
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
