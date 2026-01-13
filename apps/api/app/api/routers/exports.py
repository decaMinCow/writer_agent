from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BriefSnapshot, SnapshotGlossaryEntry
from app.db.session import get_db_session
from app.schemas.exports import (
    ExportResponse,
    GlossaryEntryCreate,
    GlossaryEntryRead,
    GlossaryEntryUpdate,
)
from app.services.export_compiler import (
    compile_novel_markdown,
    compile_novel_text,
    compile_script_fountain,
)

router = APIRouter(prefix="/api/brief-snapshots", tags=["exports"])


async def _get_snapshot(session: AsyncSession, snapshot_id: uuid.UUID) -> BriefSnapshot:
    snap = await session.get(BriefSnapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="brief_snapshot_not_found")
    return snap


@router.get("/{snapshot_id}/glossary", response_model=list[GlossaryEntryRead])
async def list_glossary_entries(
    snapshot_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[GlossaryEntryRead]:
    await _get_snapshot(session, snapshot_id)

    result = await session.execute(
        select(SnapshotGlossaryEntry)
        .where(SnapshotGlossaryEntry.brief_snapshot_id == snapshot_id)
        .order_by(SnapshotGlossaryEntry.term.asc())
    )
    return [GlossaryEntryRead.model_validate(item) for item in result.scalars().all()]


@router.post("/{snapshot_id}/glossary", response_model=GlossaryEntryRead)
async def create_glossary_entry(
    snapshot_id: uuid.UUID,
    payload: GlossaryEntryCreate,
    session: AsyncSession = Depends(get_db_session),
) -> GlossaryEntryRead:
    await _get_snapshot(session, snapshot_id)

    entry = SnapshotGlossaryEntry(
        brief_snapshot_id=snapshot_id,
        term=payload.term,
        replacement=payload.replacement,
        meta=payload.meta,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return GlossaryEntryRead.model_validate(entry)


@router.patch("/{snapshot_id}/glossary/{entry_id}", response_model=GlossaryEntryRead)
async def update_glossary_entry(
    snapshot_id: uuid.UUID,
    entry_id: uuid.UUID,
    payload: GlossaryEntryUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> GlossaryEntryRead:
    await _get_snapshot(session, snapshot_id)
    entry = await session.get(SnapshotGlossaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="glossary_entry_not_found")
    if entry.brief_snapshot_id != snapshot_id:
        raise HTTPException(status_code=400, detail="glossary_entry_not_in_snapshot")

    if payload.term is not None:
        entry.term = payload.term
    if payload.replacement is not None:
        entry.replacement = payload.replacement
    if payload.meta is not None:
        entry.meta = payload.meta

    await session.commit()
    await session.refresh(entry)
    return GlossaryEntryRead.model_validate(entry)


@router.get("/{snapshot_id}/export/novel.md", response_model=ExportResponse)
async def export_novel_markdown(
    snapshot_id: uuid.UUID,
    apply_glossary: bool = True,
    session: AsyncSession = Depends(get_db_session),
) -> ExportResponse:
    await _get_snapshot(session, snapshot_id)
    text = await compile_novel_markdown(
        session=session, brief_snapshot_id=snapshot_id, apply_glossary=apply_glossary
    )
    return ExportResponse(filename="novel.md", content_type="text/markdown; charset=utf-8", text=text)


@router.get("/{snapshot_id}/export/novel.txt", response_model=ExportResponse)
async def export_novel_text(
    snapshot_id: uuid.UUID,
    apply_glossary: bool = True,
    session: AsyncSession = Depends(get_db_session),
) -> ExportResponse:
    await _get_snapshot(session, snapshot_id)
    text = await compile_novel_text(
        session=session, brief_snapshot_id=snapshot_id, apply_glossary=apply_glossary
    )
    return ExportResponse(filename="novel.txt", content_type="text/plain; charset=utf-8", text=text)


@router.get("/{snapshot_id}/export/script.fountain", response_model=ExportResponse)
async def export_script_fountain(
    snapshot_id: uuid.UUID,
    apply_glossary: bool = True,
    session: AsyncSession = Depends(get_db_session),
) -> ExportResponse:
    await _get_snapshot(session, snapshot_id)
    text = await compile_script_fountain(
        session=session, brief_snapshot_id=snapshot_id, apply_glossary=apply_glossary
    )
    return ExportResponse(
        filename="script.fountain",
        content_type="text/plain; charset=utf-8",
        text=text,
    )

