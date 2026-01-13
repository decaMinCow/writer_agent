from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BriefSnapshot
from app.db.session import get_db_session
from app.services import cascade_delete

router = APIRouter(prefix="/api/brief-snapshots", tags=["brief-snapshots"])


@router.delete("/{snapshot_id}")
async def delete_brief_snapshot(
    snapshot_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    snapshot = await session.get(BriefSnapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="brief_snapshot_not_found")

    await cascade_delete.delete_brief_snapshot(
        session=session, snapshot_id=snapshot.id, app=request.app
    )
    return {"deleted": True}

