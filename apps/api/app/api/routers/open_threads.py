from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ArtifactVersion, BriefSnapshot, OpenThread, OpenThreadRef
from app.db.session import get_db_session
from app.schemas.open_threads import (
    OpenThreadCreate,
    OpenThreadRead,
    OpenThreadRefCreate,
    OpenThreadRefRead,
    OpenThreadUpdate,
)

router = APIRouter(prefix="/api/brief-snapshots", tags=["open-threads"])


async def _get_snapshot(session: AsyncSession, snapshot_id: uuid.UUID) -> BriefSnapshot:
    snap = await session.get(BriefSnapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="brief_snapshot_not_found")
    return snap


async def _get_thread(
    session: AsyncSession, *, snapshot_id: uuid.UUID, thread_id: uuid.UUID
) -> OpenThread:
    thread = await session.get(OpenThread, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="open_thread_not_found")
    if thread.brief_snapshot_id != snapshot_id:
        raise HTTPException(status_code=400, detail="open_thread_not_in_snapshot")
    return thread


@router.post("/{snapshot_id}/threads", response_model=OpenThreadRead)
async def create_open_thread(
    snapshot_id: uuid.UUID,
    payload: OpenThreadCreate,
    session: AsyncSession = Depends(get_db_session),
) -> OpenThreadRead:
    await _get_snapshot(session, snapshot_id)

    thread = OpenThread(
        brief_snapshot_id=snapshot_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        meta=payload.meta,
    )
    session.add(thread)
    await session.commit()
    await session.refresh(thread)
    return OpenThreadRead.model_validate(thread)


@router.get("/{snapshot_id}/threads", response_model=list[OpenThreadRead])
async def list_open_threads(
    snapshot_id: uuid.UUID,
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[OpenThreadRead]:
    await _get_snapshot(session, snapshot_id)

    stmt = select(OpenThread).where(OpenThread.brief_snapshot_id == snapshot_id)
    if status:
        stmt = stmt.where(OpenThread.status == status)
    stmt = stmt.order_by(OpenThread.updated_at.desc(), OpenThread.created_at.desc())

    result = await session.execute(stmt)
    return [OpenThreadRead.model_validate(item) for item in result.scalars().all()]


@router.patch("/{snapshot_id}/threads/{thread_id}", response_model=OpenThreadRead)
async def update_open_thread(
    snapshot_id: uuid.UUID,
    thread_id: uuid.UUID,
    payload: OpenThreadUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> OpenThreadRead:
    thread = await _get_thread(session, snapshot_id=snapshot_id, thread_id=thread_id)

    if payload.title is not None:
        thread.title = payload.title
    if payload.description is not None:
        thread.description = payload.description
    if payload.status is not None:
        thread.status = payload.status
    if payload.meta is not None:
        thread.meta = payload.meta

    await session.commit()
    await session.refresh(thread)
    return OpenThreadRead.model_validate(thread)


@router.post("/{snapshot_id}/threads/{thread_id}/refs", response_model=OpenThreadRefRead)
async def add_open_thread_ref(
    snapshot_id: uuid.UUID,
    thread_id: uuid.UUID,
    payload: OpenThreadRefCreate,
    session: AsyncSession = Depends(get_db_session),
) -> OpenThreadRefRead:
    await _get_snapshot(session, snapshot_id)
    thread = await _get_thread(session, snapshot_id=snapshot_id, thread_id=thread_id)

    version = await session.get(ArtifactVersion, payload.artifact_version_id)
    if not version:
        raise HTTPException(status_code=404, detail="artifact_version_not_found")
    if version.brief_snapshot_id != snapshot_id:
        raise HTTPException(status_code=400, detail="artifact_version_not_in_snapshot")

    ref = OpenThreadRef(
        thread_id=thread.id,
        artifact_version_id=payload.artifact_version_id,
        ref_kind=payload.ref_kind,
        quote=payload.quote,
        meta=payload.meta,
    )
    session.add(ref)
    await session.commit()
    await session.refresh(ref)
    return OpenThreadRefRead.model_validate(ref)


@router.get("/{snapshot_id}/threads/{thread_id}/refs", response_model=list[OpenThreadRefRead])
async def list_open_thread_refs(
    snapshot_id: uuid.UUID,
    thread_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[OpenThreadRefRead]:
    await _get_snapshot(session, snapshot_id)
    thread = await _get_thread(session, snapshot_id=snapshot_id, thread_id=thread_id)

    result = await session.execute(
        select(OpenThreadRef)
        .where(OpenThreadRef.thread_id == thread.id)
        .order_by(OpenThreadRef.created_at.asc())
    )
    return [OpenThreadRefRead.model_validate(item) for item in result.scalars().all()]

