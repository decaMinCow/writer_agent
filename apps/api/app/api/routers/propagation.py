from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Artifact,
    ArtifactImpact,
    ArtifactVersion,
    ArtifactVersionSource,
    BriefSnapshot,
    PropagationEvent,
)
from app.db.session import get_db_session
from app.schemas.propagation import (
    ArtifactImpactRead,
    ImpactReportItem,
    PropagationApplyRequest,
    PropagationApplyResponse,
    PropagationEventRead,
    PropagationPreviewRequest,
    PropagationPreviewResponse,
    PropagationRepairRequest,
    PropagationRepairResponse,
    RepairedArtifactVersion,
)
from app.services.memory_store import index_artifact_version
from app.services.propagation_extraction import extract_fact_changes, repair_impacted_content

router = APIRouter(prefix="/api/brief-snapshots", tags=["propagation"])


async def _get_snapshot(session: AsyncSession, snapshot_id: uuid.UUID) -> BriefSnapshot:
    snap = await session.get(BriefSnapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="brief_snapshot_not_found")
    return snap


async def _get_artifact(session: AsyncSession, artifact_id: uuid.UUID) -> Artifact:
    artifact = await session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    return artifact


async def _get_artifact_version(session: AsyncSession, version_id: uuid.UUID) -> ArtifactVersion:
    version = await session.get(ArtifactVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="artifact_version_not_found")
    return version


async def _select_latest_artifact_versions_for_snapshot(
    *, session: AsyncSession, brief_snapshot_id: uuid.UUID
) -> list[tuple[Artifact, ArtifactVersion]]:
    result = await session.execute(
        select(Artifact, ArtifactVersion)
        .join(ArtifactVersion, ArtifactVersion.artifact_id == Artifact.id)
        .where(ArtifactVersion.brief_snapshot_id == brief_snapshot_id)
        .order_by(Artifact.id.asc(), ArtifactVersion.created_at.desc())
    )
    rows = result.all()

    chosen: dict[uuid.UUID, tuple[Artifact, ArtifactVersion]] = {}
    for artifact, version in rows:
        if artifact.id in chosen:
            continue
        chosen[artifact.id] = (artifact, version)

    def sort_key(item: tuple[Artifact, ArtifactVersion]) -> tuple[str, int, str]:
        artifact, version = item
        ordinal = artifact.ordinal if artifact.ordinal is not None else 10**9
        return (str(artifact.kind.value), int(ordinal), str(version.created_at))

    return sorted(chosen.values(), key=sort_key)


def _basic_fact_changes(*, base_text: str, edited_text: str) -> str:
    base = (base_text or "").strip()
    edited = (edited_text or "").strip()

    base_len = len(base)
    edited_len = len(edited)
    base_lines = len(base.splitlines()) if base else 0
    edited_lines = len(edited.splitlines()) if edited else 0

    delta_len = edited_len - base_len
    delta_lines = edited_lines - base_lines

    return (
        "文本已修改（LLM 未启用/不可用，以下为基础统计摘要）：\n"
        f"- 字数：{base_len} → {edited_len}（{delta_len:+d}）\n"
        f"- 行数：{base_lines} → {edited_lines}（{delta_lines:+d}）\n"
        "- 建议：检查后续章节/场景是否与本次改动一致。"
    )


def _artifact_meta_for_llm(*, artifact: Artifact, version: ArtifactVersion) -> dict[str, Any]:
    return {
        "artifact_id": str(artifact.id),
        "artifact_version_id": str(version.id),
        "kind": str(artifact.kind.value),
        "ordinal": artifact.ordinal,
        "title": artifact.title,
        "version_metadata": dict(version.meta or {}),
        "created_at": version.created_at.isoformat(),
    }


async def _compute_impacts(
    *,
    session: AsyncSession,
    brief_snapshot_id: uuid.UUID,
    edited_artifact: Artifact,
) -> list[tuple[Artifact, ArtifactVersion, str]]:
    sources = await _select_latest_artifact_versions_for_snapshot(
        session=session,
        brief_snapshot_id=brief_snapshot_id,
    )

    impacts: list[tuple[Artifact, ArtifactVersion, str]] = []
    edited_ordinal = edited_artifact.ordinal
    for artifact, version in sources:
        if artifact.id == edited_artifact.id:
            continue
        if artifact.kind != edited_artifact.kind:
            continue

        is_downstream = (
            edited_ordinal is None
            or artifact.ordinal is None
            or int(artifact.ordinal) > int(edited_ordinal)
        )
        if not is_downstream:
            continue

        reason = (
            f"上游 {edited_artifact.kind.value}（ordinal={edited_artifact.ordinal}）发生编辑改动，"
            "下游内容可能需要同步修订。"
        )
        impacts.append((artifact, version, reason))

    return impacts


@router.get("/{snapshot_id}/impacts", response_model=list[ArtifactImpactRead])
async def list_impacts(
    snapshot_id: uuid.UUID,
    include_repaired: bool = False,
    session: AsyncSession = Depends(get_db_session),
) -> list[ArtifactImpactRead]:
    await _get_snapshot(session, snapshot_id)

    stmt = select(ArtifactImpact).where(ArtifactImpact.brief_snapshot_id == snapshot_id)
    if not include_repaired:
        stmt = stmt.where(ArtifactImpact.repaired_artifact_version_id.is_(None))
    stmt = stmt.order_by(ArtifactImpact.created_at.asc())

    result = await session.execute(stmt)
    return [ArtifactImpactRead.model_validate(item) for item in result.scalars().all()]


@router.post("/{snapshot_id}/propagation/preview", response_model=PropagationPreviewResponse)
async def preview_propagation(
    snapshot_id: uuid.UUID,
    payload: PropagationPreviewRequest,
    request: Request,
    use_llm: bool = False,
    session: AsyncSession = Depends(get_db_session),
) -> PropagationPreviewResponse:
    snapshot = await _get_snapshot(session, snapshot_id)

    base_version = await _get_artifact_version(session, payload.base_artifact_version_id)
    edited_version = await _get_artifact_version(session, payload.edited_artifact_version_id)

    if base_version.brief_snapshot_id != snapshot.id or edited_version.brief_snapshot_id != snapshot.id:
        raise HTTPException(status_code=400, detail="artifact_versions_not_in_snapshot")

    edited_artifact = await _get_artifact(session, edited_version.artifact_id)

    impacts = await _compute_impacts(
        session=session,
        brief_snapshot_id=snapshot.id,
        edited_artifact=edited_artifact,
    )

    llm = getattr(request.app.state, "llm_client", None)
    patches: dict[str, Any] = {}
    if use_llm and llm is not None:
        base_artifact = await _get_artifact(session, base_version.artifact_id)
        result = await extract_fact_changes(
            llm=llm,
            brief_json=dict(snapshot.content or {}),
            base_meta=_artifact_meta_for_llm(artifact=base_artifact, version=base_version),
            edited_meta=_artifact_meta_for_llm(artifact=edited_artifact, version=edited_version),
            base_text=base_version.content_text,
            edited_text=edited_version.content_text,
        )
        fact_changes = (result.fact_changes or "").strip() or _basic_fact_changes(
            base_text=base_version.content_text, edited_text=edited_version.content_text
        )
        patches = dict(result.patches or {})
    else:
        fact_changes = _basic_fact_changes(
            base_text=base_version.content_text, edited_text=edited_version.content_text
        )

    return PropagationPreviewResponse(
        fact_changes=fact_changes,
        impacts=[
            ImpactReportItem(
                artifact_id=artifact.id,
                artifact_version_id=version.id,
                kind=artifact.kind,
                ordinal=artifact.ordinal,
                title=artifact.title,
                reason=reason,
            )
            for artifact, version, reason in impacts
        ],
        patches=patches,
    )


@router.post("/{snapshot_id}/propagation/apply", response_model=PropagationApplyResponse)
async def apply_propagation(
    snapshot_id: uuid.UUID,
    payload: PropagationApplyRequest,
    request: Request,
    use_llm: bool = False,
    session: AsyncSession = Depends(get_db_session),
) -> PropagationApplyResponse:
    snapshot = await _get_snapshot(session, snapshot_id)

    base_version = await _get_artifact_version(session, payload.base_artifact_version_id)
    edited_version = await _get_artifact_version(session, payload.edited_artifact_version_id)

    if base_version.brief_snapshot_id != snapshot.id or edited_version.brief_snapshot_id != snapshot.id:
        raise HTTPException(status_code=400, detail="artifact_versions_not_in_snapshot")

    edited_artifact = await _get_artifact(session, edited_version.artifact_id)
    impacts = await _compute_impacts(
        session=session,
        brief_snapshot_id=snapshot.id,
        edited_artifact=edited_artifact,
    )

    llm = getattr(request.app.state, "llm_client", None)
    patches: dict[str, Any] = {}
    if use_llm and llm is not None:
        base_artifact = await _get_artifact(session, base_version.artifact_id)
        diff = await extract_fact_changes(
            llm=llm,
            brief_json=dict(snapshot.content or {}),
            base_meta=_artifact_meta_for_llm(artifact=base_artifact, version=base_version),
            edited_meta=_artifact_meta_for_llm(artifact=edited_artifact, version=edited_version),
            base_text=base_version.content_text,
            edited_text=edited_version.content_text,
        )
        fact_changes = (diff.fact_changes or "").strip() or _basic_fact_changes(
            base_text=base_version.content_text, edited_text=edited_version.content_text
        )
        patches = dict(diff.patches or {})
    else:
        fact_changes = _basic_fact_changes(
            base_text=base_version.content_text, edited_text=edited_version.content_text
        )

    event = PropagationEvent(
        brief_snapshot_id=snapshot.id,
        base_artifact_version_id=base_version.id,
        edited_artifact_version_id=edited_version.id,
        fact_changes=fact_changes,
        meta={"patches": patches},
    )
    session.add(event)
    await session.flush()

    artifact_ids = [artifact.id for artifact, _version, _reason in impacts]
    if artifact_ids:
        await session.execute(
            delete(ArtifactImpact).where(
                ArtifactImpact.brief_snapshot_id == snapshot.id,
                ArtifactImpact.artifact_id.in_(artifact_ids),
                ArtifactImpact.repaired_artifact_version_id.is_(None),
            )
        )

    created_impacts: list[ArtifactImpact] = []
    for artifact, version, reason in impacts:
        impact = ArtifactImpact(
            propagation_event_id=event.id,
            brief_snapshot_id=snapshot.id,
            artifact_id=artifact.id,
            artifact_version_id=version.id,
            reason=reason,
            repaired_artifact_version_id=None,
            repaired_at=None,
        )
        session.add(impact)
        created_impacts.append(impact)

    await session.commit()
    await session.refresh(event)
    for impact in created_impacts:
        await session.refresh(impact)

    return PropagationApplyResponse(
        event=PropagationEventRead.model_validate(event),
        impacts=[ArtifactImpactRead.model_validate(item) for item in created_impacts],
    )


@router.post(
    "/{snapshot_id}/propagation/events/{event_id}/repair", response_model=PropagationRepairResponse
)
async def repair_impacts(
    snapshot_id: uuid.UUID,
    event_id: uuid.UUID,
    payload: PropagationRepairRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> PropagationRepairResponse:
    snapshot = await _get_snapshot(session, snapshot_id)

    event = await session.get(PropagationEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="propagation_event_not_found")
    if event.brief_snapshot_id != snapshot.id:
        raise HTTPException(status_code=400, detail="propagation_event_not_in_snapshot")

    llm = getattr(request.app.state, "llm_client", None)
    if llm is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    upstream_edited = await _get_artifact_version(session, event.edited_artifact_version_id)

    stmt = select(ArtifactImpact).where(
        ArtifactImpact.brief_snapshot_id == snapshot.id,
        ArtifactImpact.propagation_event_id == event.id,
        ArtifactImpact.repaired_artifact_version_id.is_(None),
    )
    if payload.artifact_ids:
        stmt = stmt.where(ArtifactImpact.artifact_id.in_(payload.artifact_ids))
    stmt = stmt.order_by(ArtifactImpact.created_at.asc())

    impacts = (await session.execute(stmt)).scalars().all()

    repaired: list[RepairedArtifactVersion] = []
    updated_impacts: list[ArtifactImpact] = []

    for impact in impacts:
        artifact = await _get_artifact(session, impact.artifact_id)
        impacted_version = await _get_artifact_version(session, impact.artifact_version_id)

        repaired_text = await repair_impacted_content(
            llm=llm,
            brief_json=dict(snapshot.content or {}),
            fact_changes=event.fact_changes,
            upstream_edited_text=upstream_edited.content_text,
            impacted_meta=_artifact_meta_for_llm(artifact=artifact, version=impacted_version),
            impacted_text=impacted_version.content_text,
        )

        new_version = ArtifactVersion(
            artifact_id=artifact.id,
            source=ArtifactVersionSource.agent,
            content_text=repaired_text,
            meta={
                "repaired_from_version_id": str(impacted_version.id),
                "propagation_event_id": str(event.id),
                "upstream_edited_version_id": str(upstream_edited.id),
            },
            workflow_run_id=None,
            brief_snapshot_id=snapshot.id,
        )
        session.add(new_version)
        await session.commit()
        await session.refresh(new_version)

        impact.repaired_artifact_version_id = new_version.id
        impact.repaired_at = datetime.datetime.now(datetime.UTC)
        await session.commit()
        await session.refresh(impact)

        repaired.append(
            RepairedArtifactVersion(artifact_id=artifact.id, artifact_version_id=new_version.id)
        )
        updated_impacts.append(impact)

        embeddings = getattr(request.app.state, "embeddings_client", None)
        if embeddings is not None:
            try:
                await index_artifact_version(
                    session=session,
                    embeddings=embeddings,
                    brief_snapshot_id=snapshot.id,
                    artifact_version_id=new_version.id,
                    content_text=repaired_text,
                    meta={
                        "kind": str(artifact.kind.value),
                        "ordinal": artifact.ordinal,
                        "source": str(ArtifactVersionSource.agent.value),
                        "propagation_event_id": str(event.id),
                    },
                )
            except Exception:
                await session.rollback()

    return PropagationRepairResponse(
        repaired=repaired,
        impacts=[ArtifactImpactRead.model_validate(item) for item in updated_impacts],
    )
