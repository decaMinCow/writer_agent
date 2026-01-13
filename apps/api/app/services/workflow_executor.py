from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Artifact,
    ArtifactKind,
    ArtifactVersion,
    ArtifactVersionSource,
    BriefSnapshot,
    RunStatus,
    WorkflowKind,
    WorkflowRun,
    WorkflowStepRun,
)
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.schemas.generation import (
    CriticResult,
    DraftResult,
    NovelBeats,
    NovelOutline,
    RewriteResult,
    ScriptSceneList,
)
from app.services.json_utils import deep_merge
from app.services.memory_store import index_artifact_version, retrieve_evidence
from app.services.prompting import extract_json_object, load_prompt, render_prompt
from app.services.text_utils import apply_replacements, join_paragraphs, numbered_paragraphs


def _now() -> datetime:
    return datetime.now().astimezone()


def _cursor(state: dict[str, Any]) -> dict[str, Any]:
    cursor = state.get("cursor")
    if isinstance(cursor, dict):
        return cursor
    cursor = {"phase": None}
    state["cursor"] = cursor
    return cursor


async def _select_latest_novel_chapter_versions(
    *,
    session: AsyncSession,
    brief_snapshot_id: uuid.UUID,
) -> list[tuple[int, Artifact, ArtifactVersion]]:
    result = await session.execute(
        select(Artifact, ArtifactVersion)
        .join(ArtifactVersion, ArtifactVersion.artifact_id == Artifact.id)
        .where(Artifact.kind == ArtifactKind.novel_chapter)
        .where(ArtifactVersion.brief_snapshot_id == brief_snapshot_id)
        .order_by(Artifact.ordinal.asc().nullslast(), ArtifactVersion.created_at.desc())
    )
    rows = result.all()

    chosen: dict[int, tuple[int, Artifact, ArtifactVersion]] = {}
    for artifact, version in rows:
        if artifact.ordinal is None:
            continue
        ordinal = int(artifact.ordinal)
        if ordinal in chosen:
            continue
        chosen[ordinal] = (ordinal, artifact, version)

    return [chosen[idx] for idx in sorted(chosen.keys())]


def _novel_digest_lines(digests: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in digests:
        idx = item.get("chapter_index") or item.get("index")
        title = item.get("chapter_title") or item.get("title") or ""
        fact = item.get("fact_digest") or ""
        if idx:
            prefix = f"第{idx}章"
            if title:
                prefix += f"《{title}》"
            if fact:
                lines.append(f"{prefix}：{fact}")
            else:
                lines.append(prefix)
    return "\n".join(lines)


async def _get_snapshot(session: AsyncSession, snapshot_id: uuid.UUID) -> BriefSnapshot:
    snap = await session.get(BriefSnapshot, snapshot_id)
    if not snap:
        raise RuntimeError("brief_snapshot_not_found")
    return snap


async def _get_or_create_artifact(
    *,
    session: AsyncSession,
    kind: ArtifactKind,
    ordinal: int,
    title: str | None,
) -> Artifact:
    result = await session.execute(
        select(Artifact).where(Artifact.kind == kind, Artifact.ordinal == ordinal)
    )
    artifact = result.scalars().first()
    if artifact:
        if title and artifact.title != title:
            artifact.title = title
            await session.commit()
            await session.refresh(artifact)
        return artifact

    artifact = Artifact(kind=kind, ordinal=ordinal, title=title)
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)
    return artifact


async def execute_next_step(
    *,
    session: AsyncSession,
    llm: LLMClient,
    embeddings: EmbeddingsClient,
    run: WorkflowRun,
) -> dict[str, Any]:
    state: dict[str, Any] = dict(run.state or {})
    cursor = _cursor(state)

    snapshot = await _get_snapshot(session, run.brief_snapshot_id)
    brief_json = snapshot.content
    current_state: dict[str, Any] = dict(state.get("current_state") or {})

    if run.kind == WorkflowKind.novel:
        phase = cursor.get("phase") or "novel_outline"
        chapter_index = int(cursor.get("chapter_index") or 1)

        if phase == "novel_outline":
            raw = await llm.complete(
                system_prompt=load_prompt("novel_outline_system.md"),
                user_prompt=render_prompt(
                    load_prompt("novel_outline_user.md"),
                    {"BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2)},
                ),
            )
            payload = extract_json_object(raw)
            outline = NovelOutline.model_validate(payload)
            state["outline"] = outline.model_dump(mode="json")
            cursor["phase"] = "novel_beats"
            run.state = state
            await session.commit()
            return {"phase": phase, "outline": state["outline"]}

        if phase == "novel_beats":
            outline_json = state.get("outline") or {}
            raw = await llm.complete(
                system_prompt=load_prompt("novel_beats_system.md"),
                user_prompt=render_prompt(
                    load_prompt("novel_beats_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "OUTLINE_JSON": json.dumps(outline_json, ensure_ascii=False, indent=2),
                    },
                ),
            )
            payload = extract_json_object(raw)
            beats = NovelBeats.model_validate(payload)
            state["beats"] = beats.model_dump(mode="json")
            cursor["phase"] = "novel_chapter_draft"
            cursor["chapter_index"] = 1
            state["fix_attempt"] = 0
            run.state = state
            await session.commit()
            return {"phase": phase, "beats": state["beats"]}

        beats_json = state.get("beats") or {}
        beats = NovelBeats.model_validate(beats_json)
        if chapter_index > len(beats.chapters):
            run.status = RunStatus.succeeded
            cursor["phase"] = "done"
            run.state = state
            await session.commit()
            return {"phase": "done"}

        chapter = beats.chapters[chapter_index - 1]

        if phase == "novel_chapter_draft":
            query = f"第{chapter.index}章 {chapter.title} {','.join(chapter.beats[:3])}"
            evidence_chunks = await retrieve_evidence(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                query=query,
                limit=6,
            )
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await llm.complete(
                system_prompt=load_prompt("novel_draft_system.md"),
                user_prompt=render_prompt(
                    load_prompt("novel_draft_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "CHAPTER_INDEX": str(chapter.index),
                        "CHAPTER_TITLE": chapter.title,
                        "CHAPTER_BEATS_JSON": json.dumps(chapter.beats, ensure_ascii=False),
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
            )
            payload = extract_json_object(raw)
            draft = DraftResult.model_validate(payload)
            state["draft"] = {"kind": "chapter", "index": chapter.index, "title": draft.title, "text": draft.text}
            cursor["phase"] = "novel_chapter_critic"
            run.state = state
            await session.commit()
            return {"phase": phase, "chapter_index": chapter.index, "draft_preview": draft.text[:500]}

        if phase == "novel_chapter_critic":
            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")
            paragraphs, numbered = numbered_paragraphs(draft_text)
            query = f"Critic 第{chapter.index}章 {chapter.title}"
            evidence_chunks = await retrieve_evidence(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                query=query,
                limit=6,
            )
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await llm.complete(
                system_prompt=load_prompt("critic_system.md"),
                user_prompt=render_prompt(
                    load_prompt("critic_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
            )
            payload = extract_json_object(raw)
            critic = CriticResult.model_validate(payload)
            state["critic"] = critic.model_dump(mode="json")

            fix_attempt = int(state.get("fix_attempt") or 0)
            if not critic.hard_pass or critic.rewrite_paragraph_indices:
                if fix_attempt >= 2:
                    run.status = RunStatus.failed
                    run.error = {"detail": "max_fix_attempts_exceeded", "hard_errors": critic.hard_errors}
                    run.state = state
                    await session.commit()
                    return {"phase": phase, "hard_pass": False, "hard_errors": critic.hard_errors}
                cursor["phase"] = "novel_chapter_fix"
            else:
                cursor["phase"] = "novel_chapter_commit"

            run.state = state
            await session.commit()
            return {
                "phase": phase,
                "hard_pass": critic.hard_pass,
                "hard_errors": critic.hard_errors,
                "soft_scores": critic.soft_scores,
                "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
            }

        if phase == "novel_chapter_fix":
            critic_json = state.get("critic") or {}
            critic = CriticResult.model_validate(critic_json)
            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")
            paragraphs, numbered = numbered_paragraphs(draft_text)

            raw = await llm.complete(
                system_prompt=load_prompt("rewrite_system.md"),
                user_prompt=render_prompt(
                    load_prompt("rewrite_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "REWRITE_INSTRUCTIONS": critic.rewrite_instructions or "提升一致性与质量",
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "REWRITE_PARAGRAPH_INDICES_JSON": json.dumps(
                            critic.rewrite_paragraph_indices, ensure_ascii=False
                        ),
                    },
                ),
            )
            payload = extract_json_object(raw)
            rewrite = RewriteResult.model_validate(payload)
            replacements = {int(k): v for k, v in rewrite.replacements.items()}
            updated_paragraphs = apply_replacements(paragraphs, replacements)
            new_text = join_paragraphs(updated_paragraphs)
            state["draft"] = {
                "kind": "chapter",
                "index": chapter.index,
                "title": draft_state.get("title"),
                "text": new_text,
            }
            state["fix_attempt"] = int(state.get("fix_attempt") or 0) + 1
            cursor["phase"] = "novel_chapter_critic"
            run.state = state
            await session.commit()
            return {"phase": phase, "updated_preview": new_text[:500]}

        if phase == "novel_chapter_commit":
            critic_json = state.get("critic") or {}
            critic = CriticResult.model_validate(critic_json)
            if not critic.hard_pass:
                run.status = RunStatus.failed
                run.error = {"detail": "hard_check_failed", "hard_errors": critic.hard_errors}
                run.state = state
                await session.commit()
                return {"phase": phase, "hard_pass": False, "hard_errors": critic.hard_errors}

            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")
            draft_title = (draft_state.get("title") or chapter.title) if draft_state else chapter.title

            artifact = await _get_or_create_artifact(
                session=session,
                kind=ArtifactKind.novel_chapter,
                ordinal=chapter.index,
                title=str(draft_title),
            )
            version = ArtifactVersion(
                artifact_id=artifact.id,
                source=ArtifactVersionSource.agent,
                content_text=draft_text,
                meta={
                    "fact_digest": critic.fact_digest,
                    "tone_digest": critic.tone_digest,
                    "soft_scores": critic.soft_scores,
                    "chapter_index": chapter.index,
                    "chapter_title": str(draft_title),
                },
                workflow_run_id=run.id,
                brief_snapshot_id=snapshot.id,
            )
            session.add(version)
            await session.commit()
            await session.refresh(version)

            await index_artifact_version(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                artifact_version_id=version.id,
                content_text=draft_text,
                meta={"kind": "novel_chapter", "ordinal": chapter.index},
            )

            current_state = deep_merge(current_state, critic.state_patch)
            state["current_state"] = current_state
            state.pop("draft", None)
            state.pop("critic", None)
            state["fix_attempt"] = 0

            cursor["chapter_index"] = chapter.index + 1
            cursor["phase"] = "novel_chapter_draft"
            if cursor["chapter_index"] > len(beats.chapters):
                run.status = RunStatus.succeeded
                cursor["phase"] = "done"

            run.state = state
            await session.commit()
            return {
                "phase": phase,
                "artifact_id": str(artifact.id),
                "artifact_version_id": str(version.id),
                "fact_digest": critic.fact_digest,
                "tone_digest": critic.tone_digest,
            }

        raise RuntimeError(f"unknown_phase:{phase}")

    if run.kind == WorkflowKind.script:
        phase = cursor.get("phase") or "script_scene_list"
        scene_index = int(cursor.get("scene_index") or 1)

        if phase == "script_scene_list":
            raw = await llm.complete(
                system_prompt=load_prompt("script_scene_list_system.md"),
                user_prompt=render_prompt(
                    load_prompt("script_scene_list_user.md"),
                    {"BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2)},
                ),
            )
            payload = extract_json_object(raw)
            scene_list = ScriptSceneList.model_validate(payload)
            state["scene_list"] = scene_list.model_dump(mode="json")
            cursor["phase"] = "script_scene_draft"
            cursor["scene_index"] = 1
            state["fix_attempt"] = 0
            run.state = state
            await session.commit()
            return {"phase": phase, "scene_list": state["scene_list"]}

        scene_list_json = state.get("scene_list") or {}
        scene_list = ScriptSceneList.model_validate(scene_list_json)
        if scene_index > len(scene_list.scenes):
            run.status = RunStatus.succeeded
            cursor["phase"] = "done"
            run.state = state
            await session.commit()
            return {"phase": "done"}

        scene = scene_list.scenes[scene_index - 1]

        if phase == "script_scene_draft":
            output_spec = dict((brief_json.get("output_spec") or {}) if isinstance(brief_json, dict) else {})
            query = f"Scene {scene.slug} {scene.title} {scene.location} {scene.time}"
            evidence_chunks = await retrieve_evidence(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                query=query,
                limit=6,
            )
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await llm.complete(
                system_prompt=load_prompt("script_scene_draft_system.md"),
                user_prompt=render_prompt(
                    load_prompt("script_scene_draft_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "SCENE_JSON": json.dumps(
                            deep_merge(scene.model_dump(mode="json"), {"output_spec": output_spec}),
                            ensure_ascii=False,
                            indent=2,
                        ),
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
            )
            payload = extract_json_object(raw)
            draft = DraftResult.model_validate(payload)
            state["draft"] = {"kind": "scene", "index": scene.index, "slug": scene.slug, "text": draft.text}
            cursor["phase"] = "script_scene_critic"
            run.state = state
            await session.commit()
            return {"phase": phase, "scene_index": scene.index, "draft_preview": draft.text[:500]}

        if phase == "script_scene_critic":
            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")
            paragraphs, numbered = numbered_paragraphs(draft_text)
            query = f"Critic Scene {scene.slug} {scene.title}"
            evidence_chunks = await retrieve_evidence(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                query=query,
                limit=6,
            )
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await llm.complete(
                system_prompt=load_prompt("critic_system.md"),
                user_prompt=render_prompt(
                    load_prompt("critic_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
            )
            payload = extract_json_object(raw)
            critic = CriticResult.model_validate(payload)
            state["critic"] = critic.model_dump(mode="json")

            fix_attempt = int(state.get("fix_attempt") or 0)
            if not critic.hard_pass or critic.rewrite_paragraph_indices:
                if fix_attempt >= 2:
                    run.status = RunStatus.failed
                    run.error = {"detail": "max_fix_attempts_exceeded", "hard_errors": critic.hard_errors}
                    run.state = state
                    await session.commit()
                    return {"phase": phase, "hard_pass": False, "hard_errors": critic.hard_errors}
                cursor["phase"] = "script_scene_fix"
            else:
                cursor["phase"] = "script_scene_commit"

            run.state = state
            await session.commit()
            return {
                "phase": phase,
                "hard_pass": critic.hard_pass,
                "hard_errors": critic.hard_errors,
                "soft_scores": critic.soft_scores,
                "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
            }

        if phase == "script_scene_fix":
            critic_json = state.get("critic") or {}
            critic = CriticResult.model_validate(critic_json)
            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")
            paragraphs, numbered = numbered_paragraphs(draft_text)

            raw = await llm.complete(
                system_prompt=load_prompt("rewrite_system.md"),
                user_prompt=render_prompt(
                    load_prompt("rewrite_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "REWRITE_INSTRUCTIONS": critic.rewrite_instructions or "提升一致性与质量",
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "REWRITE_PARAGRAPH_INDICES_JSON": json.dumps(
                            critic.rewrite_paragraph_indices, ensure_ascii=False
                        ),
                    },
                ),
            )
            payload = extract_json_object(raw)
            rewrite = RewriteResult.model_validate(payload)
            replacements = {int(k): v for k, v in rewrite.replacements.items()}
            updated_paragraphs = apply_replacements(paragraphs, replacements)
            new_text = join_paragraphs(updated_paragraphs)
            state["draft"] = {"kind": "scene", "index": scene.index, "slug": scene.slug, "text": new_text}
            state["fix_attempt"] = int(state.get("fix_attempt") or 0) + 1
            cursor["phase"] = "script_scene_critic"
            run.state = state
            await session.commit()
            return {"phase": phase, "updated_preview": new_text[:500]}

        if phase == "script_scene_commit":
            critic_json = state.get("critic") or {}
            critic = CriticResult.model_validate(critic_json)
            if not critic.hard_pass:
                run.status = RunStatus.failed
                run.error = {"detail": "hard_check_failed", "hard_errors": critic.hard_errors}
                run.state = state
                await session.commit()
                return {"phase": phase, "hard_pass": False, "hard_errors": critic.hard_errors}

            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")

            artifact = await _get_or_create_artifact(
                session=session,
                kind=ArtifactKind.script_scene,
                ordinal=scene.index,
                title=scene.title,
            )
            version = ArtifactVersion(
                artifact_id=artifact.id,
                source=ArtifactVersionSource.agent,
                content_text=draft_text,
                meta={
                    "fact_digest": critic.fact_digest,
                    "tone_digest": critic.tone_digest,
                    "soft_scores": critic.soft_scores,
                    "scene_index": scene.index,
                    "scene_slug": scene.slug,
                    "scene_title": scene.title,
                },
                workflow_run_id=run.id,
                brief_snapshot_id=snapshot.id,
            )
            session.add(version)
            await session.commit()
            await session.refresh(version)

            await index_artifact_version(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                artifact_version_id=version.id,
                content_text=draft_text,
                meta={"kind": "script_scene", "ordinal": scene.index},
            )

            current_state = deep_merge(current_state, critic.state_patch)
            state["current_state"] = current_state
            state.pop("draft", None)
            state.pop("critic", None)
            state["fix_attempt"] = 0

            cursor["scene_index"] = scene.index + 1
            cursor["phase"] = "script_scene_draft"
            if cursor["scene_index"] > len(scene_list.scenes):
                run.status = RunStatus.succeeded
                cursor["phase"] = "done"

            run.state = state
            await session.commit()
            return {
                "phase": phase,
                "artifact_id": str(artifact.id),
                "artifact_version_id": str(version.id),
                "fact_digest": critic.fact_digest,
                "tone_digest": critic.tone_digest,
            }

        raise RuntimeError(f"unknown_phase:{phase}")

    if run.kind == WorkflowKind.novel_to_script:
        phase = cursor.get("phase") or "nts_scene_list"
        scene_index = int(cursor.get("scene_index") or 1)

        if phase == "nts_scene_list":
            sources = await _select_latest_novel_chapter_versions(
                session=session,
                brief_snapshot_id=snapshot.id,
            )
            if not sources:
                run.status = RunStatus.failed
                run.error = {"detail": "novel_source_missing"}
                cursor["phase"] = "failed"
                run.state = state
                await session.commit()
                return {"phase": phase, "detail": "novel_source_missing"}

            digests: list[dict[str, Any]] = []
            source_version_ids: list[str] = []
            for ordinal, artifact, version in sources:
                meta = dict(version.meta or {})
                fact_digest = str(meta.get("fact_digest") or "").strip()
                tone_digest = str(meta.get("tone_digest") or "").strip()
                chapter_title = str(
                    meta.get("chapter_title")
                    or meta.get("title")
                    or artifact.title
                    or f"第{ordinal}章"
                )
                if not fact_digest:
                    fact_digest = (version.content_text or "").strip()[:200]
                digests.append(
                    {
                        "chapter_index": ordinal,
                        "chapter_title": chapter_title,
                        "fact_digest": fact_digest,
                        "tone_digest": tone_digest,
                    }
                )
                source_version_ids.append(str(version.id))

            state["novel_source"] = {"artifact_version_ids": source_version_ids, "chapter_digests": digests}

            raw = await llm.complete(
                system_prompt=load_prompt("nts_scene_list_system.md"),
                user_prompt=render_prompt(
                    load_prompt("nts_scene_list_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "NOVEL_CHAPTER_DIGESTS_JSON": json.dumps(
                            digests, ensure_ascii=False, indent=2
                        ),
                    },
                ),
            )
            payload = extract_json_object(raw)
            scene_list = ScriptSceneList.model_validate(payload)
            state["scene_list"] = scene_list.model_dump(mode="json")
            cursor["phase"] = "nts_scene_draft"
            cursor["scene_index"] = 1
            state["fix_attempt"] = 0
            run.state = state
            await session.commit()
            return {"phase": phase, "scene_list": state["scene_list"]}

        scene_list_json = state.get("scene_list") or {}
        scene_list = ScriptSceneList.model_validate(scene_list_json)
        if scene_index > len(scene_list.scenes):
            run.status = RunStatus.succeeded
            cursor["phase"] = "done"
            run.state = state
            await session.commit()
            return {"phase": "done"}

        scene = scene_list.scenes[scene_index - 1]
        source = state.get("novel_source") or {}
        chapter_digests = (
            list(source.get("chapter_digests") or []) if isinstance(source, dict) else []
        )
        digest_lines = _novel_digest_lines(chapter_digests)

        if phase == "nts_scene_draft":
            output_spec = dict((brief_json.get("output_spec") or {}) if isinstance(brief_json, dict) else {})
            query = f"NTS Scene {scene.slug} {scene.title} {scene.location} {scene.time} {' '.join(scene.characters)} {scene.purpose}"
            evidence_chunks = await retrieve_evidence(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                query=query,
                limit=8,
            )
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            if digest_lines:
                evidence_text = (digest_lines + ("\n\n---\n\n" + evidence_text if evidence_text else "")).strip()

            raw = await llm.complete(
                system_prompt=load_prompt("nts_scene_draft_system.md"),
                user_prompt=render_prompt(
                    load_prompt("nts_scene_draft_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "SCENE_JSON": json.dumps(
                            deep_merge(scene.model_dump(mode="json"), {"output_spec": output_spec}),
                            ensure_ascii=False,
                            indent=2,
                        ),
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
            )
            payload = extract_json_object(raw)
            draft = DraftResult.model_validate(payload)
            state["draft"] = {"kind": "scene", "index": scene.index, "slug": scene.slug, "text": draft.text}
            cursor["phase"] = "nts_scene_critic"
            run.state = state
            await session.commit()
            return {"phase": phase, "scene_index": scene.index, "draft_preview": draft.text[:500]}

        if phase == "nts_scene_critic":
            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")
            paragraphs, numbered = numbered_paragraphs(draft_text)

            query = f"NTS Critic {scene.slug} {scene.title}"
            evidence_chunks = await retrieve_evidence(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                query=query,
                limit=8,
            )
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            if digest_lines:
                evidence_text = (digest_lines + ("\n\n---\n\n" + evidence_text if evidence_text else "")).strip()

            raw = await llm.complete(
                system_prompt=load_prompt("nts_critic_system.md"),
                user_prompt=render_prompt(
                    load_prompt("nts_critic_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
            )
            payload = extract_json_object(raw)
            critic = CriticResult.model_validate(payload)
            state["critic"] = critic.model_dump(mode="json")

            fix_attempt = int(state.get("fix_attempt") or 0)
            if not critic.hard_pass or critic.rewrite_paragraph_indices:
                if fix_attempt >= 2:
                    run.status = RunStatus.failed
                    run.error = {"detail": "max_fix_attempts_exceeded", "hard_errors": critic.hard_errors}
                    run.state = state
                    await session.commit()
                    return {"phase": phase, "hard_pass": False, "hard_errors": critic.hard_errors}
                cursor["phase"] = "nts_scene_fix"
            else:
                cursor["phase"] = "nts_scene_commit"

            run.state = state
            await session.commit()
            return {
                "phase": phase,
                "hard_pass": critic.hard_pass,
                "hard_errors": critic.hard_errors,
                "soft_scores": critic.soft_scores,
                "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
            }

        if phase == "nts_scene_fix":
            critic_json = state.get("critic") or {}
            critic = CriticResult.model_validate(critic_json)
            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")
            paragraphs, numbered = numbered_paragraphs(draft_text)

            raw = await llm.complete(
                system_prompt=load_prompt("rewrite_system.md"),
                user_prompt=render_prompt(
                    load_prompt("rewrite_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "REWRITE_INSTRUCTIONS": critic.rewrite_instructions or "提升一致性与质量",
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "REWRITE_PARAGRAPH_INDICES_JSON": json.dumps(
                            critic.rewrite_paragraph_indices, ensure_ascii=False
                        ),
                    },
                ),
            )
            payload = extract_json_object(raw)
            rewrite = RewriteResult.model_validate(payload)
            replacements = {int(k): v for k, v in rewrite.replacements.items()}
            updated_paragraphs = apply_replacements(paragraphs, replacements)
            new_text = join_paragraphs(updated_paragraphs)
            state["draft"] = {"kind": "scene", "index": scene.index, "slug": scene.slug, "text": new_text}
            state["fix_attempt"] = int(state.get("fix_attempt") or 0) + 1
            cursor["phase"] = "nts_scene_critic"
            run.state = state
            await session.commit()
            return {"phase": phase, "updated_preview": new_text[:500]}

        if phase == "nts_scene_commit":
            critic_json = state.get("critic") or {}
            critic = CriticResult.model_validate(critic_json)
            if not critic.hard_pass:
                run.status = RunStatus.failed
                run.error = {"detail": "hard_check_failed", "hard_errors": critic.hard_errors}
                run.state = state
                await session.commit()
                return {"phase": phase, "hard_pass": False, "hard_errors": critic.hard_errors}

            draft_state = state.get("draft") or {}
            draft_text = str(draft_state.get("text") or "")

            artifact = await _get_or_create_artifact(
                session=session,
                kind=ArtifactKind.script_scene,
                ordinal=scene.index,
                title=scene.title,
            )
            version = ArtifactVersion(
                artifact_id=artifact.id,
                source=ArtifactVersionSource.agent,
                content_text=draft_text,
                meta={
                    "fact_digest": critic.fact_digest,
                    "tone_digest": critic.tone_digest,
                    "soft_scores": critic.soft_scores,
                    "scene_index": scene.index,
                    "scene_slug": scene.slug,
                    "scene_title": scene.title,
                    "source_kind": "novel_to_script",
                },
                workflow_run_id=run.id,
                brief_snapshot_id=snapshot.id,
            )
            session.add(version)
            await session.commit()
            await session.refresh(version)

            await index_artifact_version(
                session=session,
                embeddings=embeddings,
                brief_snapshot_id=snapshot.id,
                artifact_version_id=version.id,
                content_text=draft_text,
                meta={"kind": "script_scene", "ordinal": scene.index},
            )

            current_state = deep_merge(current_state, critic.state_patch)
            state["current_state"] = current_state
            state.pop("draft", None)
            state.pop("critic", None)
            state["fix_attempt"] = 0

            cursor["scene_index"] = scene.index + 1
            cursor["phase"] = "nts_scene_draft"
            if cursor["scene_index"] > len(scene_list.scenes):
                run.status = RunStatus.succeeded
                cursor["phase"] = "done"

            run.state = state
            await session.commit()
            return {
                "phase": phase,
                "artifact_id": str(artifact.id),
                "artifact_version_id": str(version.id),
                "fact_digest": critic.fact_digest,
                "tone_digest": critic.tone_digest,
            }

        raise RuntimeError(f"unknown_phase:{phase}")

    raise RuntimeError(f"unsupported_workflow_kind:{run.kind}")


async def execute_next_step_safe(
    *,
    session: AsyncSession,
    llm: LLMClient,
    embeddings: EmbeddingsClient,
    run: WorkflowRun,
    step_name: str,
    step_index: int,
) -> WorkflowStepRun:
    step_run = WorkflowStepRun(
        workflow_run_id=run.id,
        step_name=step_name,
        step_index=step_index,
        status=RunStatus.running,
        outputs={},
        started_at=_now(),
    )
    session.add(step_run)
    await session.commit()
    await session.refresh(step_run)

    try:
        outputs = await execute_next_step(session=session, llm=llm, embeddings=embeddings, run=run)
        step_run.status = RunStatus.succeeded
        step_run.outputs = outputs
        step_run.finished_at = _now()
        await session.commit()
        await session.refresh(step_run)
        return step_run
    except (ValidationError, RuntimeError) as exc:
        step_run.status = RunStatus.failed
        step_run.error = str(exc)
        step_run.finished_at = _now()
        run.status = RunStatus.failed
        run.error = {"detail": "step_failed", "error": str(exc)}
        await session.commit()
        await session.refresh(step_run)
        return step_run
