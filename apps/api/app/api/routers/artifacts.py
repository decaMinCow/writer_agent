from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artifact, ArtifactVersion, ArtifactVersionSource, BriefSnapshot
from app.db.session import get_db_session
from app.schemas.artifacts import (
    ArtifactCreate,
    ArtifactRead,
    ArtifactVersionCreate,
    ArtifactVersionRead,
    ArtifactVersionRewriteRequest,
)
from app.services.memory_store import index_artifact_version
from app.services.targeted_rewrite import rewrite_selected_text

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.post("", response_model=ArtifactRead)
async def create_artifact(
    payload: ArtifactCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ArtifactRead:
    artifact = Artifact(kind=payload.kind, title=payload.title, ordinal=payload.ordinal)
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)
    return ArtifactRead.model_validate(artifact)


@router.get("", response_model=list[ArtifactRead])
async def list_artifacts(session: AsyncSession = Depends(get_db_session)) -> list[ArtifactRead]:
    result = await session.execute(select(Artifact).order_by(Artifact.updated_at.desc()))
    items = result.scalars().all()
    return [ArtifactRead.model_validate(item) for item in items]


@router.get("/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(
    artifact_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ArtifactRead:
    artifact = await session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    return ArtifactRead.model_validate(artifact)


@router.post("/{artifact_id}/versions", response_model=ArtifactVersionRead)
async def create_artifact_version(
    artifact_id: uuid.UUID,
    request: Request,
    payload: ArtifactVersionCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ArtifactVersionRead:
    artifact = await session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact_not_found")

    version = ArtifactVersion(
        artifact_id=artifact.id,
        source=payload.source,
        content_text=payload.content_text,
        meta=payload.meta,
        workflow_run_id=payload.workflow_run_id,
        brief_snapshot_id=payload.brief_snapshot_id,
    )
    session.add(version)
    await session.commit()
    await session.refresh(version)
    response = ArtifactVersionRead.model_validate(version)

    brief_snapshot_id = payload.brief_snapshot_id
    if brief_snapshot_id:
        embeddings = getattr(request.app.state, "embeddings_client", None)
        if embeddings is not None:
            try:
                await index_artifact_version(
                    session=session,
                    embeddings=embeddings,
                    brief_snapshot_id=brief_snapshot_id,
                    artifact_version_id=version.id,
                    content_text=payload.content_text,
                    meta={
                        "kind": str(artifact.kind.value),
                        "ordinal": artifact.ordinal,
                        "source": str(payload.source.value),
                    },
                )
            except Exception:
                await session.rollback()

    return response


@router.get("/{artifact_id}/versions", response_model=list[ArtifactVersionRead])
async def list_artifact_versions(
    artifact_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[ArtifactVersionRead]:
    artifact = await session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact_not_found")

    result = await session.execute(
        select(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == artifact.id)
        .order_by(ArtifactVersion.created_at.desc())
    )
    items = result.scalars().all()
    return [ArtifactVersionRead.model_validate(item) for item in items]


@router.get("/versions/{version_id}", response_model=ArtifactVersionRead)
async def get_artifact_version(
    version_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ArtifactVersionRead:
    version = await session.get(ArtifactVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="artifact_version_not_found")
    return ArtifactVersionRead.model_validate(version)


@router.post("/versions/{version_id}/rewrite", response_model=ArtifactVersionRead)
async def rewrite_artifact_version(
    version_id: uuid.UUID,
    request: Request,
    payload: ArtifactVersionRewriteRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ArtifactVersionRead:
    base_version = await session.get(ArtifactVersion, version_id)
    if not base_version:
        raise HTTPException(status_code=404, detail="artifact_version_not_found")

    artifact = await session.get(Artifact, base_version.artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact_not_found")

    llm = getattr(request.app.state, "llm_client", None)
    if llm is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    brief_json: dict[str, object] = {}
    if base_version.brief_snapshot_id:
        snap = await session.get(BriefSnapshot, base_version.brief_snapshot_id)
        if snap:
            brief_json = dict(snap.content or {})

    text = base_version.content_text or ""
    if payload.selection_start is None or payload.selection_end is None:
        selection_start = 0
        selection_end = len(text)
    else:
        selection_start = int(payload.selection_start)
        selection_end = int(payload.selection_end)

    if selection_start < 0 or selection_end < 0 or selection_start > selection_end:
        raise HTTPException(status_code=400, detail="invalid_selection_range")
    if selection_end > len(text):
        raise HTTPException(status_code=400, detail="invalid_selection_range")
    if selection_start == selection_end:
        raise HTTPException(status_code=400, detail="empty_selection_range")

    before = text[:selection_start]
    selected = text[selection_start:selection_end]
    after = text[selection_end:]

    replacement = await rewrite_selected_text(
        llm=llm,
        brief_json=brief_json,
        artifact_meta={
            "artifact_id": str(artifact.id),
            "artifact_version_id": str(base_version.id),
            "kind": str(artifact.kind.value),
            "ordinal": artifact.ordinal,
            "title": artifact.title,
            "brief_snapshot_id": str(base_version.brief_snapshot_id) if base_version.brief_snapshot_id else None,
        },
        instruction=payload.instruction,
        selected_text=selected,
        context_before=before[-400:],
        context_after=after[:400],
    )
    if not replacement.strip():
        raise HTTPException(status_code=400, detail="rewrite_empty")

    new_text = before + replacement + after

    version = ArtifactVersion(
        artifact_id=artifact.id,
        source=ArtifactVersionSource.agent,
        content_text=new_text,
        meta={
            "rewritten_from_version_id": str(base_version.id),
            "rewrite_instruction": payload.instruction,
            "selection_start": selection_start,
            "selection_end": selection_end,
        },
        workflow_run_id=base_version.workflow_run_id,
        brief_snapshot_id=base_version.brief_snapshot_id,
    )
    session.add(version)
    await session.commit()
    await session.refresh(version)
    response = ArtifactVersionRead.model_validate(version)

    if base_version.brief_snapshot_id:
        embeddings = getattr(request.app.state, "embeddings_client", None)
        if embeddings is not None:
            try:
                await index_artifact_version(
                    session=session,
                    embeddings=embeddings,
                    brief_snapshot_id=base_version.brief_snapshot_id,
                    artifact_version_id=version.id,
                    content_text=new_text,
                    meta={
                        "kind": str(artifact.kind.value),
                        "ordinal": artifact.ordinal,
                        "source": str(ArtifactVersionSource.agent.value),
                        "rewritten_from_version_id": str(base_version.id),
                    },
                )
            except Exception:
                await session.rollback()

    return response
