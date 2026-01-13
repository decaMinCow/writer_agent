from __future__ import annotations

import asyncio
import uuid

from fastapi import FastAPI
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Artifact,
    ArtifactImpact,
    ArtifactVersion,
    Brief,
    BriefMessage,
    BriefSnapshot,
    KgEntity,
    KgEvent,
    KgRelation,
    LintIssue,
    MemoryChunk,
    OpenThread,
    OpenThreadRef,
    PropagationEvent,
    SnapshotGlossaryEntry,
    WorkflowRun,
    WorkflowStepRun,
)


def stop_autorun_best_effort(*, app: FastAPI | None, run_id: uuid.UUID) -> None:
    if app is None:
        return

    flags = getattr(app.state, "workflow_autorun_stop_flags", None)
    if isinstance(flags, dict):
        stop_event = flags.get(run_id)
        if isinstance(stop_event, asyncio.Event):
            stop_event.set()

    tasks = getattr(app.state, "workflow_autorun_tasks", None)
    if isinstance(tasks, dict):
        task = tasks.get(run_id)
        if task is not None and not getattr(task, "done", lambda: True)():
            task.cancel()


async def cleanup_orphan_artifacts(*, session: AsyncSession) -> None:
    await session.execute(
        delete(Artifact).where(~Artifact.id.in_(select(ArtifactVersion.artifact_id)))
    )


async def delete_workflow_run(
    *,
    session: AsyncSession,
    run_id: uuid.UUID,
    app: FastAPI | None = None,
) -> None:
    stop_autorun_best_effort(app=app, run_id=run_id)

    version_ids = select(ArtifactVersion.id).where(ArtifactVersion.workflow_run_id == run_id)

    await session.execute(
        delete(OpenThreadRef).where(OpenThreadRef.artifact_version_id.in_(version_ids))
    )

    event_ids = select(PropagationEvent.id).where(
        or_(
            PropagationEvent.base_artifact_version_id.in_(version_ids),
            PropagationEvent.edited_artifact_version_id.in_(version_ids),
        )
    )

    await session.execute(
        delete(ArtifactImpact).where(
            or_(
                ArtifactImpact.propagation_event_id.in_(event_ids),
                ArtifactImpact.artifact_version_id.in_(version_ids),
                ArtifactImpact.repaired_artifact_version_id.in_(version_ids),
            )
        )
    )
    await session.execute(delete(PropagationEvent).where(PropagationEvent.id.in_(event_ids)))

    await session.execute(delete(LintIssue).where(LintIssue.artifact_version_id.in_(version_ids)))
    await session.execute(delete(KgEvent).where(KgEvent.artifact_version_id.in_(version_ids)))
    await session.execute(delete(MemoryChunk).where(MemoryChunk.artifact_version_id.in_(version_ids)))

    await session.execute(delete(WorkflowStepRun).where(WorkflowStepRun.workflow_run_id == run_id))
    await session.execute(delete(ArtifactVersion).where(ArtifactVersion.id.in_(version_ids)))
    await session.execute(delete(WorkflowRun).where(WorkflowRun.id == run_id))

    await cleanup_orphan_artifacts(session=session)
    await session.commit()


async def delete_brief_snapshot(
    *,
    session: AsyncSession,
    snapshot_id: uuid.UUID,
    app: FastAPI | None = None,
) -> None:
    run_ids = (
        await session.execute(
            select(WorkflowRun.id).where(WorkflowRun.brief_snapshot_id == snapshot_id)
        )
    ).scalars().all()
    for run_id in run_ids:
        stop_autorun_best_effort(app=app, run_id=run_id)

    run_ids_subq = select(WorkflowRun.id).where(WorkflowRun.brief_snapshot_id == snapshot_id)

    thread_ids_subq = select(OpenThread.id).where(OpenThread.brief_snapshot_id == snapshot_id)
    await session.execute(delete(OpenThreadRef).where(OpenThreadRef.thread_id.in_(thread_ids_subq)))

    await session.execute(delete(ArtifactImpact).where(ArtifactImpact.brief_snapshot_id == snapshot_id))
    await session.execute(
        delete(PropagationEvent).where(PropagationEvent.brief_snapshot_id == snapshot_id)
    )
    await session.execute(delete(LintIssue).where(LintIssue.brief_snapshot_id == snapshot_id))

    await session.execute(delete(KgRelation).where(KgRelation.brief_snapshot_id == snapshot_id))
    await session.execute(delete(KgEvent).where(KgEvent.brief_snapshot_id == snapshot_id))
    await session.execute(delete(KgEntity).where(KgEntity.brief_snapshot_id == snapshot_id))

    await session.execute(
        delete(SnapshotGlossaryEntry).where(SnapshotGlossaryEntry.brief_snapshot_id == snapshot_id)
    )
    await session.execute(delete(MemoryChunk).where(MemoryChunk.brief_snapshot_id == snapshot_id))

    await session.execute(delete(WorkflowStepRun).where(WorkflowStepRun.workflow_run_id.in_(run_ids_subq)))
    await session.execute(
        delete(ArtifactVersion).where(
            or_(
                ArtifactVersion.brief_snapshot_id == snapshot_id,
                ArtifactVersion.workflow_run_id.in_(run_ids_subq),
            )
        )
    )
    await session.execute(delete(WorkflowRun).where(WorkflowRun.brief_snapshot_id == snapshot_id))

    await session.execute(delete(OpenThread).where(OpenThread.brief_snapshot_id == snapshot_id))
    await session.execute(delete(BriefSnapshot).where(BriefSnapshot.id == snapshot_id))

    await cleanup_orphan_artifacts(session=session)
    await session.commit()


async def delete_brief(
    *,
    session: AsyncSession,
    brief_id: uuid.UUID,
    app: FastAPI | None = None,
) -> None:
    snapshot_ids = (
        await session.execute(select(BriefSnapshot.id).where(BriefSnapshot.brief_id == brief_id))
    ).scalars().all()
    for snapshot_id in snapshot_ids:
        await delete_brief_snapshot(session=session, snapshot_id=snapshot_id, app=app)

    await session.execute(delete(BriefMessage).where(BriefMessage.brief_id == brief_id))
    await session.execute(delete(Brief).where(Brief.id == brief_id))

    await session.commit()

