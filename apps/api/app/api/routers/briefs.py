from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Brief, BriefMessage, BriefMessageRole, BriefSnapshot
from app.db.session import get_db_session
from app.schemas.brief_messages import (
    BriefMessageCreate,
    BriefMessageCreateResponse,
    BriefMessageRead,
)
from app.schemas.briefs import (
    BriefCreate,
    BriefRead,
    BriefSnapshotCreate,
    BriefSnapshotRead,
    BriefUpdate,
    OutputSpecPatch,
)
from app.services.brief_builder import build_brief_result
from app.services.settings_store import get_output_spec_defaults

router = APIRouter(prefix="/api/briefs", tags=["briefs"])


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@router.post("", response_model=BriefRead)
async def create_brief(
    payload: BriefCreate,
    session: AsyncSession = Depends(get_db_session),
) -> BriefRead:
    brief = Brief(title=payload.title, content=payload.content.model_dump(mode="json", exclude_none=True))
    session.add(brief)
    await session.commit()
    await session.refresh(brief)
    return BriefRead.model_validate(brief)


@router.get("", response_model=list[BriefRead])
async def list_briefs(session: AsyncSession = Depends(get_db_session)) -> list[BriefRead]:
    result = await session.execute(select(Brief).order_by(Brief.updated_at.desc()))
    items = result.scalars().all()
    return [BriefRead.model_validate(item) for item in items]


@router.get("/{brief_id}", response_model=BriefRead)
async def get_brief(
    brief_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> BriefRead:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")
    return BriefRead.model_validate(brief)


@router.patch("/{brief_id}", response_model=BriefRead)
async def update_brief(
    brief_id: uuid.UUID,
    payload: BriefUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> BriefRead:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")

    if payload.title is not None:
        brief.title = payload.title
    if payload.content is not None:
        brief.content = payload.content.model_dump(mode="json", exclude_none=True)

    await session.commit()
    await session.refresh(brief)
    return BriefRead.model_validate(brief)


@router.post("/{brief_id}/snapshots", response_model=BriefSnapshotRead)
async def create_snapshot(
    brief_id: uuid.UUID,
    payload: BriefSnapshotCreate,
    session: AsyncSession = Depends(get_db_session),
) -> BriefSnapshotRead:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")

    content = dict(brief.content or {})
    output_spec_overrides = dict(content.get("output_spec") or {})
    defaults = await get_output_spec_defaults(session=session)
    content["output_spec"] = _deep_merge(defaults, output_spec_overrides)

    snapshot = BriefSnapshot(brief_id=brief.id, label=payload.label, content=content)
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return BriefSnapshotRead.model_validate(snapshot)


@router.get("/{brief_id}/snapshots", response_model=list[BriefSnapshotRead])
async def list_snapshots(
    brief_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[BriefSnapshotRead]:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")

    result = await session.execute(
        select(BriefSnapshot)
        .where(BriefSnapshot.brief_id == brief.id)
        .order_by(BriefSnapshot.created_at.desc())
    )
    items = result.scalars().all()
    return [BriefSnapshotRead.model_validate(item) for item in items]


@router.patch("/{brief_id}/output-spec", response_model=BriefRead)
async def patch_output_spec(
    brief_id: uuid.UUID,
    payload: OutputSpecPatch,
    session: AsyncSession = Depends(get_db_session),
) -> BriefRead:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")

    content = dict(brief.content or {})
    output_spec = dict(content.get("output_spec") or {})

    if "language" in payload.model_fields_set:
        if payload.language is None:
            output_spec.pop("language", None)
        else:
            output_spec["language"] = payload.language

    if "script_format" in payload.model_fields_set:
        if payload.script_format is None:
            output_spec.pop("script_format", None)
        else:
            output_spec["script_format"] = payload.script_format.value

    if "script_format_notes" in payload.model_fields_set:
        if payload.script_format_notes is None:
            output_spec.pop("script_format_notes", None)
        else:
            output_spec["script_format_notes"] = payload.script_format_notes

    content["output_spec"] = output_spec
    brief.content = content

    await session.commit()
    await session.refresh(brief)
    return BriefRead.model_validate(brief)


@router.get("/{brief_id}/messages", response_model=list[BriefMessageRead])
async def list_brief_messages(
    brief_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    limit: int = 100,
) -> list[BriefMessageRead]:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")

    limit = max(1, min(limit, 500))
    result = await session.execute(
        select(BriefMessage)
        .where(BriefMessage.brief_id == brief.id)
        .order_by(BriefMessage.created_at.asc())
        .limit(limit)
    )
    items = result.scalars().all()
    return [BriefMessageRead.model_validate(item) for item in items]


@router.post("/{brief_id}/messages", response_model=BriefMessageCreateResponse)
async def add_brief_message(
    brief_id: uuid.UUID,
    payload: BriefMessageCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> BriefMessageCreateResponse:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")

    session.add(
        BriefMessage(
            brief_id=brief.id,
            role=BriefMessageRole.user,
            content_text=payload.content_text,
            meta={"mode": payload.mode.value},
        )
    )
    await session.commit()

    llm = getattr(request.app.state, "llm_client", None)
    if llm is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    current_brief_json: dict[str, Any] = {"title": brief.title, "content": brief.content}
    try:
        result = await build_brief_result(
            llm=llm,
            current_brief_json=current_brief_json,
            mode=payload.mode,
            user_message=payload.content_text,
        )
    except RuntimeError:
        raise HTTPException(status_code=502, detail="brief_builder_failed") from None

    patch = result.brief_patch
    new_content = dict(brief.content or {})
    if patch.content:
        new_content = _deep_merge(new_content, patch.content)
    if patch.title is not None:
        brief.title = patch.title
        new_content = _deep_merge(new_content, {"title": patch.title})

    brief.content = new_content
    session.add(brief)

    session.add(
        BriefMessage(
            brief_id=brief.id,
            role=BriefMessageRole.assistant,
            content_text=result.assistant_message,
            meta={
                "gap_report": result.gap_report.model_dump(mode="json"),
                "brief_patch": result.brief_patch.model_dump(mode="json"),
            },
        )
    )

    await session.commit()
    await session.refresh(brief)

    result_messages = await session.execute(
        select(BriefMessage)
        .where(BriefMessage.brief_id == brief.id)
        .order_by(BriefMessage.created_at.asc())
        .limit(200)
    )
    messages = [BriefMessageRead.model_validate(item) for item in result_messages.scalars().all()]

    return BriefMessageCreateResponse(
        brief=BriefRead.model_validate(brief),
        gap_report=result.gap_report,
        messages=messages,
    )
