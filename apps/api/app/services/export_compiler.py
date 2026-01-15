from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artifact, ArtifactKind, ArtifactVersion, SnapshotGlossaryEntry


async def _latest_versions_by_kind(
    *,
    session: AsyncSession,
    brief_snapshot_id: uuid.UUID,
    kind: ArtifactKind,
) -> list[tuple[Artifact, ArtifactVersion]]:
    result = await session.execute(
        select(Artifact, ArtifactVersion)
        .join(ArtifactVersion, ArtifactVersion.artifact_id == Artifact.id)
        .where(Artifact.kind == kind)
        .where(ArtifactVersion.brief_snapshot_id == brief_snapshot_id)
        .order_by(Artifact.ordinal.asc().nullslast(), ArtifactVersion.created_at.desc())
    )
    rows = result.all()

    chosen: dict[int, tuple[Artifact, ArtifactVersion]] = {}
    for artifact, version in rows:
        if artifact.ordinal is None:
            continue
        ordinal = int(artifact.ordinal)
        if ordinal in chosen:
            continue
        chosen[ordinal] = (artifact, version)

    return [chosen[k] for k in sorted(chosen.keys())]


async def _load_glossary(
    *, session: AsyncSession, brief_snapshot_id: uuid.UUID
) -> list[tuple[str, str]]:
    result = await session.execute(
        select(SnapshotGlossaryEntry)
        .where(SnapshotGlossaryEntry.brief_snapshot_id == brief_snapshot_id)
        .order_by(SnapshotGlossaryEntry.term.asc())
    )
    entries = result.scalars().all()
    return [(e.term, e.replacement) for e in entries if e.term and e.replacement]


def _apply_glossary(text: str, replacements: list[tuple[str, str]]) -> str:
    if not replacements:
        return text
    updated = text
    for term, replacement in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        if not term:
            continue
        updated = updated.replace(term, replacement)
    return updated


async def compile_novel_markdown(
    *,
    session: AsyncSession,
    brief_snapshot_id: uuid.UUID,
    apply_glossary: bool,
) -> str:
    chapters = await _latest_versions_by_kind(
        session=session, brief_snapshot_id=brief_snapshot_id, kind=ArtifactKind.novel_chapter
    )
    replacements = await _load_glossary(session=session, brief_snapshot_id=brief_snapshot_id)
    parts: list[str] = []
    for artifact, version in chapters:
        title = artifact.title or f"第{artifact.ordinal}章"
        body = version.content_text or ""
        if apply_glossary:
            body = _apply_glossary(body, replacements)
        parts.append(f"# {title}\n\n{body}".strip())
    return "\n\n---\n\n".join(parts).strip() + ("\n" if parts else "")


async def compile_novel_text(
    *,
    session: AsyncSession,
    brief_snapshot_id: uuid.UUID,
    apply_glossary: bool,
) -> str:
    chapters = await _latest_versions_by_kind(
        session=session, brief_snapshot_id=brief_snapshot_id, kind=ArtifactKind.novel_chapter
    )
    replacements = await _load_glossary(session=session, brief_snapshot_id=brief_snapshot_id)
    parts: list[str] = []
    for artifact, version in chapters:
        title = artifact.title or f"第{artifact.ordinal}章"
        body = version.content_text or ""
        if apply_glossary:
            body = _apply_glossary(body, replacements)
        parts.append(f"{title}\n\n{body}".strip())
    return "\n\n".join(parts).strip() + ("\n" if parts else "")


def _to_fountain_scene_heading(*, artifact: Artifact) -> str:
    title = artifact.title or ""
    ordinal = artifact.ordinal
    if ordinal is None and not title:
        return "== Scene =="
    if ordinal is None:
        return f"== {title} =="
    if title:
        return f"== {ordinal}. {title} =="
    return f"== {ordinal}. =="


async def compile_script_fountain(
    *,
    session: AsyncSession,
    brief_snapshot_id: uuid.UUID,
    apply_glossary: bool,
) -> str:
    scenes = await _latest_versions_by_kind(
        session=session, brief_snapshot_id=brief_snapshot_id, kind=ArtifactKind.script_scene
    )
    replacements = await _load_glossary(session=session, brief_snapshot_id=brief_snapshot_id)
    parts: list[str] = []
    for artifact, version in scenes:
        body = version.content_text or ""
        if apply_glossary:
            body = _apply_glossary(body, replacements)
        parts.append(f"{_to_fountain_scene_heading(artifact=artifact)}\n\n{body}".strip())
    return "\n\n".join(parts).strip() + ("\n" if parts else "")


async def compile_script_text(
    *,
    session: AsyncSession,
    brief_snapshot_id: uuid.UUID,
    apply_glossary: bool,
) -> str:
    scenes = await _latest_versions_by_kind(
        session=session, brief_snapshot_id=brief_snapshot_id, kind=ArtifactKind.script_scene
    )
    replacements = await _load_glossary(session=session, brief_snapshot_id=brief_snapshot_id)
    parts: list[str] = []
    for _artifact, version in scenes:
        body = (version.content_text or "").strip()
        if apply_glossary:
            body = _apply_glossary(body, replacements)
        if body:
            parts.append(body)
    return "\n\n".join(parts).strip() + ("\n" if parts else "")
