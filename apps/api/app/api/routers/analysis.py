from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Artifact,
    ArtifactVersion,
    BriefSnapshot,
    KgEntity,
    KgEvent,
    KgRelation,
    LintIssue,
)
from app.db.session import get_db_session
from app.schemas.kg import (
    KgEntityRead,
    KgEventRead,
    KgRelationRead,
    KnowledgeGraphRead,
    KnowledgeGraphRebuildResponse,
)
from app.schemas.lint import LintIssueRead, LintRunResponse
from app.services.kg_extraction import extract_kg_for_artifact_version
from app.services.kg_store import PostgresKgStore
from app.services.prompting import extract_json_object, load_prompt, render_prompt

router = APIRouter(prefix="/api/brief-snapshots", tags=["analysis"])


async def _get_snapshot(session: AsyncSession, snapshot_id: uuid.UUID) -> BriefSnapshot:
    snap = await session.get(BriefSnapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="brief_snapshot_not_found")
    return snap


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


@router.get("/{snapshot_id}/kg", response_model=KnowledgeGraphRead)
async def get_knowledge_graph(
    snapshot_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> KnowledgeGraphRead:
    await _get_snapshot(session, snapshot_id)

    entities = (
        await session.execute(
            select(KgEntity)
            .where(KgEntity.brief_snapshot_id == snapshot_id)
            .order_by(KgEntity.created_at.asc())
        )
    ).scalars()
    relations = (
        await session.execute(
            select(KgRelation)
            .where(KgRelation.brief_snapshot_id == snapshot_id)
            .order_by(KgRelation.created_at.asc())
        )
    ).scalars()
    events = (
        await session.execute(
            select(KgEvent)
            .where(KgEvent.brief_snapshot_id == snapshot_id)
            .order_by(KgEvent.created_at.asc())
        )
    ).scalars()

    return KnowledgeGraphRead(
        entities=[KgEntityRead.model_validate(item) for item in list(entities)],
        relations=[KgRelationRead.model_validate(item) for item in list(relations)],
        events=[KgEventRead.model_validate(item) for item in list(events)],
    )


@router.post("/{snapshot_id}/kg/rebuild", response_model=KnowledgeGraphRebuildResponse)
async def rebuild_knowledge_graph(
    snapshot_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> KnowledgeGraphRebuildResponse:
    snapshot = await _get_snapshot(session, snapshot_id)

    llm = getattr(request.app.state, "llm_client", None)
    if llm is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    store = PostgresKgStore()
    await store.clear_snapshot(session=session, brief_snapshot_id=snapshot.id)

    sources = await _select_latest_artifact_versions_for_snapshot(
        session=session,
        brief_snapshot_id=snapshot.id,
    )

    entities_count = 0
    relations_count = 0
    events_count = 0

    for artifact, version in sources:
        meta = dict(version.meta or {})
        artifact_meta = {
            "artifact_id": str(artifact.id),
            "kind": str(artifact.kind.value),
            "ordinal": artifact.ordinal,
            "title": artifact.title,
            "artifact_version_id": str(version.id),
            "fact_digest": meta.get("fact_digest") or "",
            "tone_digest": meta.get("tone_digest") or "",
        }

        extracted = await extract_kg_for_artifact_version(
            llm=llm,
            brief_json=dict(snapshot.content or {}),
            artifact_meta=artifact_meta,
            content_text=version.content_text or "",
        )

        for ent in extracted.entities:
            await store.upsert_entity(
                session=session,
                brief_snapshot_id=snapshot.id,
                name=ent.name,
                entity_type=ent.entity_type,
                meta=ent.meta | {"source_artifact_version_id": str(version.id)},
            )
            entities_count += 1

        for rel in extracted.relations:
            subj = await store.upsert_entity(
                session=session,
                brief_snapshot_id=snapshot.id,
                name=rel.subject,
                entity_type=rel.subject_type or "unknown",
                meta={"source_artifact_version_id": str(version.id)},
            )
            obj = await store.upsert_entity(
                session=session,
                brief_snapshot_id=snapshot.id,
                name=rel.object,
                entity_type=rel.object_type or "unknown",
                meta={"source_artifact_version_id": str(version.id)},
            )
            await store.add_relation(
                session=session,
                brief_snapshot_id=snapshot.id,
                subject_entity_id=subj.id,
                predicate=rel.predicate,
                object_entity_id=obj.id,
                meta=rel.meta | {"source_artifact_version_id": str(version.id)},
            )
            relations_count += 1

        for event in extracted.events:
            await store.add_event(
                session=session,
                brief_snapshot_id=snapshot.id,
                summary=event.summary,
                event_key=event.event_key,
                time_hint=event.time_hint,
                artifact_version_id=version.id,
                meta=event.meta | {"source_artifact_version_id": str(version.id)},
            )
            events_count += 1

    await session.commit()

    return KnowledgeGraphRebuildResponse(
        entities_indexed=entities_count,
        relations_indexed=relations_count,
        events_indexed=events_count,
    )


@router.get("/{snapshot_id}/lint", response_model=list[LintIssueRead])
async def list_lint_issues(
    snapshot_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[LintIssueRead]:
    await _get_snapshot(session, snapshot_id)
    result = await session.execute(
        select(LintIssue)
        .where(LintIssue.brief_snapshot_id == snapshot_id)
        .order_by(LintIssue.created_at.asc())
    )
    return [LintIssueRead.model_validate(item) for item in result.scalars().all()]


@router.post("/{snapshot_id}/lint", response_model=LintRunResponse)
async def run_story_linter(
    snapshot_id: uuid.UUID,
    request: Request,
    use_llm: bool = True,
    session: AsyncSession = Depends(get_db_session),
) -> LintRunResponse:
    snapshot = await _get_snapshot(session, snapshot_id)

    sources = await _select_latest_artifact_versions_for_snapshot(
        session=session,
        brief_snapshot_id=snapshot.id,
    )

    issues: list[dict[str, Any]] = []

    # Deterministic checks (MVP).
    # 1) Duplicate ordinals per kind.
    ordinals: dict[tuple[str, int], list[str]] = {}
    for artifact, _version in sources:
        if artifact.ordinal is None:
            continue
        key = (str(artifact.kind.value), int(artifact.ordinal))
        ordinals.setdefault(key, []).append(str(artifact.id))
    for (kind, ordinal), artifact_ids in ordinals.items():
        if len(artifact_ids) > 1:
            issues.append(
                {
                    "severity": "hard",
                    "code": "duplicate_artifact_ordinal",
                    "message": f"{kind} 存在重复 ordinal={ordinal} 的 artifacts：{', '.join(artifact_ids)}",
                    "artifact_version_id": None,
                    "metadata": {"kind": kind, "ordinal": ordinal, "artifact_ids": artifact_ids},
                }
            )

    # 2) Script format basic conformance.
    output_spec = dict(
        (snapshot.content.get("output_spec") or {}) if isinstance(snapshot.content, dict) else {}
    )
    script_format = str(output_spec.get("script_format") or "")
    if script_format == "screenplay_int_ext":
        for artifact, version in sources:
            if str(artifact.kind.value) != "script_scene":
                continue
            text = version.content_text or ""
            has_heading = any(
                line.lstrip().startswith(("INT.", "EXT.")) for line in (text.splitlines() or [])
            )
            if not has_heading:
                issues.append(
                    {
                        "severity": "soft",
                        "code": "missing_int_ext_heading",
                        "message": "该场景未检测到以 INT./EXT. 开头的场景标题行（screenplay_int_ext）。",
                        "artifact_version_id": str(version.id),
                        "metadata": {"artifact_id": str(artifact.id), "ordinal": artifact.ordinal},
                    }
                )

    if use_llm:
        llm = getattr(request.app.state, "llm_client", None)
        if llm is not None:
            artifact_summaries: list[dict[str, Any]] = []
            for artifact, version in sources:
                meta = dict(version.meta or {})
                fact_digest = str(meta.get("fact_digest") or "").strip()
                if not fact_digest:
                    fact_digest = (version.content_text or "").strip()[:200]
                artifact_summaries.append(
                    {
                        "artifact_id": str(artifact.id),
                        "kind": str(artifact.kind.value),
                        "ordinal": artifact.ordinal,
                        "title": artifact.title,
                        "artifact_version_id": str(version.id),
                        "fact_digest": fact_digest,
                    }
                )

            raw = await llm.complete(
                system_prompt=load_prompt("story_lint_system.md"),
                user_prompt=render_prompt(
                    load_prompt("story_lint_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(snapshot.content, ensure_ascii=False, indent=2),
                        "ARTIFACT_SUMMARIES_JSON": json.dumps(
                            artifact_summaries, ensure_ascii=False, indent=2
                        ),
                    },
                ),
            )
            payload = extract_json_object(raw)
            llm_issues = list(payload.get("issues") or []) if isinstance(payload, dict) else []
            for item in llm_issues:
                if not isinstance(item, dict):
                    continue
                severity = str(item.get("severity") or "").strip() or "soft"
                code = str(item.get("code") or "").strip() or "llm_issue"
                message = str(item.get("message") or "").strip()
                artifact_version_id = item.get("artifact_version_id")
                if artifact_version_id is not None:
                    artifact_version_id = str(artifact_version_id)
                issues.append(
                    {
                        "severity": severity,
                        "code": code,
                        "message": message,
                        "artifact_version_id": artifact_version_id,
                        "metadata": dict(item.get("metadata") or {}),
                    }
                )

    # Persist issues (replace previous run).
    await session.execute(delete(LintIssue).where(LintIssue.brief_snapshot_id == snapshot.id))
    await session.commit()

    created: list[LintIssue] = []
    for item in issues:
        issue = LintIssue(
            brief_snapshot_id=snapshot.id,
            severity=item["severity"],
            code=item["code"],
            message=item["message"],
            artifact_version_id=uuid.UUID(item["artifact_version_id"])
            if item.get("artifact_version_id")
            else None,
            meta=item.get("metadata") or {},
        )
        session.add(issue)
        created.append(issue)

    await session.commit()
    for issue in created:
        await session.refresh(issue)

    return LintRunResponse(issues=[LintIssueRead.model_validate(item) for item in created])
