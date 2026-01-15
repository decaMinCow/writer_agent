from __future__ import annotations

import copy
import json
import re
import time
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
    EpisodeBreakdown,
    NovelBeats,
    NovelOutline,
    RewriteResult,
    ScriptSceneList,
)
from app.services.error_utils import format_exception_chain
from app.services.json_utils import deep_merge
from app.services.memory_store import index_artifact_version, retrieve_evidence
from app.services.prompting import extract_json_object, load_prompt, render_prompt
from app.services.settings_store import get_novel_to_script_prompt_defaults
from app.services.text_utils import apply_replacements, join_paragraphs, numbered_paragraphs
from app.services.workflow_events import WorkflowEventHub


def _now() -> datetime:
    return datetime.now().astimezone()


def _cursor(state: dict[str, Any]) -> dict[str, Any]:
    cursor = state.get("cursor")
    if isinstance(cursor, dict):
        return cursor
    cursor = {"phase": None}
    state["cursor"] = cursor
    return cursor


def _rag_state(state: dict[str, Any]) -> dict[str, Any]:
    rag = state.get("rag")
    if isinstance(rag, dict):
        return rag
    rag = {}
    state["rag"] = rag
    return rag


def _should_disable_embeddings(exc: BaseException) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {404, 405}:
        return True
    message = str(exc).lower()
    if "embeddings" in message and ("405" in message or "method not allowed" in message):
        return True
    return False


def _record_embeddings_error(*, state: dict[str, Any], where: str, exc: BaseException) -> None:
    rag = _rag_state(state)
    rag["last_error"] = format_exception_chain(exc)
    rag["last_error_at"] = where
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        rag["last_status_code"] = status_code
    if _should_disable_embeddings(exc):
        rag["disabled"] = True
        rag["disabled_reason"] = "embeddings_endpoint_not_supported"

 
def _rag_is_disabled(state: dict[str, Any]) -> bool:
    return bool(_rag_state(state).get("disabled"))


def _resolve_max_fix_attempts(brief_json: object) -> int:
    default = 2
    if not isinstance(brief_json, dict):
        return default
    output_spec = brief_json.get("output_spec")
    if not isinstance(output_spec, dict):
        return default
    raw = output_spec.get("max_fix_attempts")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    if value < 0:
        value = 0
    return value


_NTS_PROMPT_LEAK_MARKERS = (
    "【任务】",
    "【执行流程】",
    "短剧剧本固定格式",
    "改编规则",
    "质量要求",
    "PUA",
    "STEP1",
    "STEP2",
    "你是一名",
    "你是小说→剧本",
    "转写规范",
)

_NTS_EP_SCENE_SLUG_RE = re.compile(r"(?i)\bep(?P<ep>\d+)[_\-]s(?P<scene>\d+)\b")
_NTS_CUSTOM_SCENE_HEADER_RE = re.compile(r"(?m)^(?P<ep>\d+)\s*[-.]\s*(?P<scene>\d+)(?:\s+.*)?$")
_NTS_EPISODE_HEADER_RE = re.compile(
    r"(?m)^第(?P<ep>[0-9一二三四五六七八九十百千万亿两〇零]+)集(?P<title>.*)$"
)
_NTS_DOT_SCENE_HEADER_RE = re.compile(r"(?m)^(?P<ep>\d+)\s*[-.]\s*(?P<scene>\d+)(?:\s+.*)?$")

_CHINESE_NUMERAL_DIGITS: dict[str, int] = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_CHINESE_NUMERAL_UNITS: dict[str, int] = {"十": 10, "百": 100, "千": 1000}
_CHINESE_NUMERAL_SECTION_UNITS: dict[str, int] = {"万": 10_000, "亿": 100_000_000}


def _parse_chinese_numeral(text: str) -> int | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if all(ch in _CHINESE_NUMERAL_DIGITS or ch in _CHINESE_NUMERAL_UNITS or ch in _CHINESE_NUMERAL_SECTION_UNITS for ch in raw):
        total = 0
        section = 0
        number = 0
        for ch in raw:
            if ch in _CHINESE_NUMERAL_DIGITS:
                number = _CHINESE_NUMERAL_DIGITS[ch]
                continue
            if ch in _CHINESE_NUMERAL_UNITS:
                unit = _CHINESE_NUMERAL_UNITS[ch]
                if number == 0:
                    number = 1
                section += number * unit
                number = 0
                continue
            if ch in _CHINESE_NUMERAL_SECTION_UNITS:
                unit = _CHINESE_NUMERAL_SECTION_UNITS[ch]
                section += number
                total += section * unit
                section = 0
                number = 0
                continue
            return None
        return total + section + number
    return None


def _parse_episode_index(raw: str) -> int | None:
    value = (raw or "").strip()
    if not value:
        return None
    if value.isdigit():
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed
    return _parse_chinese_numeral(value)


def _nts_parse_episode_scene_from_slug(slug: str) -> tuple[int, int] | None:
    match = _NTS_EP_SCENE_SLUG_RE.search(slug or "")
    if not match:
        return None
    try:
        ep = int(match.group("ep"))
        scene = int(match.group("scene"))
    except (TypeError, ValueError):
        return None
    if ep < 1 or scene < 1:
        return None
    return ep, scene


def _nts_extract_custom_scene_block(*, text: str, slug: str) -> str | None:
    matches = list(_NTS_CUSTOM_SCENE_HEADER_RE.finditer(text or ""))
    if len(matches) <= 1:
        return None

    target = _nts_parse_episode_scene_from_slug(slug)
    target_index: int | None = None
    if target is not None:
        target_ep, target_scene = target
        for idx, match in enumerate(matches):
            try:
                ep = int(match.group("ep"))
                scene = int(match.group("scene"))
            except (TypeError, ValueError):
                continue
            if ep == target_ep and scene == target_scene:
                target_index = idx
                break

    if target_index is None:
        target_index = 0

    start = matches[target_index].start()
    end = matches[target_index + 1].start() if target_index + 1 < len(matches) else len(text)
    extracted = (text[start:end] or "").strip()
    return extracted or None


def _nts_scene_format_issues(*, text: str, script_format: str) -> list[str]:
    issues: list[str] = []
    if not text.strip():
        return ["empty_draft"]

    marker_hits = [m for m in _NTS_PROMPT_LEAK_MARKERS if m in text]
    if marker_hits:
        issues.append("format_prompt_leak")

    if script_format == "custom":
        headers = list(_NTS_CUSTOM_SCENE_HEADER_RE.finditer(text))
        if len(headers) > 1:
            issues.append("format_multiple_scene_blocks")
    elif script_format == "screenplay_int_ext":
        headings = re.findall(r"(?m)^(?:INT\.|EXT\.)\b", text)
        if len(headings) > 1:
            issues.append("format_multiple_scene_headings")

    return issues


def _nts_episode_format_issues(*, text: str, script_format: str, episode_index: int) -> list[str]:
    issues: list[str] = []
    if not text.strip():
        return ["empty_draft"]

    marker_hits = [m for m in _NTS_PROMPT_LEAK_MARKERS if m in text]
    if marker_hits:
        issues.append("format_prompt_leak")

    if script_format != "custom":
        return issues

    headers = list(_NTS_EPISODE_HEADER_RE.finditer(text))
    if not headers:
        issues.append("format_missing_episode_header")
    elif len(headers) > 1:
        issues.append("format_multiple_episode_headers")
    else:
        ep = _parse_episode_index(str(headers[0].group("ep") or "")) or -1
        if ep != int(episode_index):
            issues.append("format_episode_header_mismatch")

    scene_headers = list(_NTS_DOT_SCENE_HEADER_RE.finditer(text))
    if not scene_headers:
        issues.append("format_missing_scene_blocks")
        return issues

    scene_numbers: list[int] = []
    ep_mismatch = False
    for match in scene_headers:
        try:
            ep = int(match.group("ep"))
            scene_no = int(match.group("scene"))
        except (TypeError, ValueError):
            issues.append("format_scene_numbering_invalid")
            return issues
        if ep != int(episode_index):
            ep_mismatch = True
        if scene_no >= 1:
            scene_numbers.append(scene_no)
    if ep_mismatch:
        issues.append("format_scene_block_episode_mismatch")
    if scene_numbers:
        if len(scene_numbers) != len(set(scene_numbers)):
            issues.append("format_scene_blocks_duplicate")
        if scene_numbers != sorted(scene_numbers):
            issues.append("format_scene_blocks_not_monotonic")
    return issues


def _extract_episode_title(*, text: str, episode_index: int) -> str | None:
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = _NTS_EPISODE_HEADER_RE.match(stripped)
        if not match:
            continue
        ep = _parse_episode_index(str(match.group("ep") or ""))
        if ep is None:
            continue
        if ep != int(episode_index):
            continue
        title = str(match.group("title") or "").strip()
        return title or None
    return None


async def _llm_complete_with_optional_stream(
    *,
    llm: LLMClient,
    system_prompt: str,
    user_prompt: str,
    hub: WorkflowEventHub | None,
    run_id: uuid.UUID,
    step_id: uuid.UUID | None,
    step_name: str,
    flush_chars: int = 800,
    flush_interval_s: float = 0.25,
) -> str:
    if hub is None or step_id is None or not hasattr(llm, "stream_complete"):
        return await llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)

    await hub.publish(
        run_id=run_id,
        name="llm_start",
        payload={"step_id": str(step_id), "step_name": step_name},
    )

    raw_output = ""
    buffer = ""
    last_flush = time.monotonic()

    async for delta in llm.stream_complete(system_prompt=system_prompt, user_prompt=user_prompt):
        raw_output += delta
        buffer += delta
        now = time.monotonic()
        if len(buffer) >= flush_chars or (now - last_flush) >= flush_interval_s:
            await hub.publish(
                run_id=run_id,
                name="llm_delta",
                payload={"step_id": str(step_id), "append": buffer},
            )
            buffer = ""
            last_flush = now

    if buffer:
        await hub.publish(
            run_id=run_id,
            name="llm_delta",
            payload={"step_id": str(step_id), "append": buffer},
        )

    await hub.publish(run_id=run_id, name="llm_end", payload={"step_id": str(step_id)})
    return raw_output


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
    hub: WorkflowEventHub | None = None,
    step_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    # NOTE: run.state is a JSON column. Using a shallow copy can keep references to nested dicts
    # (e.g., cursor) and cause SQLAlchemy to miss changes when only nested fields are updated.
    state: dict[str, Any] = copy.deepcopy(run.state or {})
    cursor = _cursor(state)

    snapshot = await _get_snapshot(session, run.brief_snapshot_id)
    brief_json = snapshot.content
    current_state: dict[str, Any] = dict(state.get("current_state") or {})
    max_fix_attempts = _resolve_max_fix_attempts(brief_json)

    if run.kind == WorkflowKind.novel:
        phase = cursor.get("phase") or "novel_outline"
        chapter_index = int(cursor.get("chapter_index") or 1)

        if phase == "novel_outline":
            raw = await _llm_complete_with_optional_stream(
                llm=llm,
                system_prompt=load_prompt("novel_outline_system.md"),
                user_prompt=render_prompt(
                    load_prompt("novel_outline_user.md"),
                    {"BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2)},
                ),
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="novel_outline",
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
            raw = await _llm_complete_with_optional_stream(
                llm=llm,
                system_prompt=load_prompt("novel_beats_system.md"),
                user_prompt=render_prompt(
                    load_prompt("novel_beats_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                        "OUTLINE_JSON": json.dumps(outline_json, ensure_ascii=False, indent=2),
                    },
                ),
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="novel_beats",
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
            evidence_chunks = []
            if not _rag_is_disabled(state):
                try:
                    evidence_chunks = await retrieve_evidence(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=snapshot.id,
                        query=query,
                        limit=6,
                    )
                except Exception as exc:
                    _record_embeddings_error(state=state, where="novel_chapter_draft:retrieve_evidence", exc=exc)
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await _llm_complete_with_optional_stream(
                llm=llm,
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
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="novel_chapter_draft",
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
            evidence_chunks = []
            if not _rag_is_disabled(state):
                try:
                    evidence_chunks = await retrieve_evidence(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=snapshot.id,
                        query=query,
                        limit=6,
                    )
                except Exception as exc:
                    _record_embeddings_error(state=state, where="novel_chapter_critic:retrieve_evidence", exc=exc)
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await _llm_complete_with_optional_stream(
                llm=llm,
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
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="novel_chapter_critic",
            )
            payload = extract_json_object(raw)
            critic = CriticResult.model_validate(payload)
            if (not critic.hard_pass) and (not critic.rewrite_paragraph_indices) and paragraphs:
                critic.rewrite_paragraph_indices = list(range(1, len(paragraphs) + 1))
            state["critic"] = critic.model_dump(mode="json")

            fix_attempt = int(state.get("fix_attempt") or 0)
            if not critic.hard_pass or critic.rewrite_paragraph_indices:
                if fix_attempt >= max_fix_attempts:
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

            raw = await _llm_complete_with_optional_stream(
                llm=llm,
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
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="novel_chapter_fix",
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

            if not _rag_is_disabled(state):
                try:
                    await index_artifact_version(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=snapshot.id,
                        artifact_version_id=version.id,
                        content_text=draft_text,
                        meta={"kind": "novel_chapter", "ordinal": chapter.index},
                    )
                except Exception as exc:
                    await session.rollback()
                    _record_embeddings_error(state=state, where="novel_chapter_commit:index_artifact_version", exc=exc)

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
            raw = await _llm_complete_with_optional_stream(
                llm=llm,
                system_prompt=load_prompt("script_scene_list_system.md"),
                user_prompt=render_prompt(
                    load_prompt("script_scene_list_user.md"),
                    {"BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2)},
                ),
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="script_scene_list",
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
            evidence_chunks = []
            if not _rag_is_disabled(state):
                try:
                    evidence_chunks = await retrieve_evidence(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=snapshot.id,
                        query=query,
                        limit=6,
                    )
                except Exception as exc:
                    _record_embeddings_error(state=state, where="script_scene_draft:retrieve_evidence", exc=exc)
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await _llm_complete_with_optional_stream(
                llm=llm,
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
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="script_scene_draft",
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
            evidence_chunks = []
            if not _rag_is_disabled(state):
                try:
                    evidence_chunks = await retrieve_evidence(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=snapshot.id,
                        query=query,
                        limit=6,
                    )
                except Exception as exc:
                    _record_embeddings_error(state=state, where="script_scene_critic:retrieve_evidence", exc=exc)
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            raw = await _llm_complete_with_optional_stream(
                llm=llm,
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
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="script_scene_critic",
            )
            payload = extract_json_object(raw)
            critic = CriticResult.model_validate(payload)
            if (not critic.hard_pass) and (not critic.rewrite_paragraph_indices) and paragraphs:
                critic.rewrite_paragraph_indices = list(range(1, len(paragraphs) + 1))
            state["critic"] = critic.model_dump(mode="json")

            fix_attempt = int(state.get("fix_attempt") or 0)
            if not critic.hard_pass or critic.rewrite_paragraph_indices:
                if fix_attempt >= max_fix_attempts:
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

            raw = await _llm_complete_with_optional_stream(
                llm=llm,
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
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="script_scene_fix",
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

            if not _rag_is_disabled(state):
                try:
                    await index_artifact_version(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=snapshot.id,
                        artifact_version_id=version.id,
                        content_text=draft_text,
                        meta={"kind": "script_scene", "ordinal": scene.index},
                    )
                except Exception as exc:
                    await session.rollback()
                    _record_embeddings_error(state=state, where="script_scene_commit:index_artifact_version", exc=exc)

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
        # Default to episode-based conversion (1 chapter = 1 episode). Keep `nts_scene_*` phases
        # for backward-compatible runs that were started with the older scene workflow.
        phase = cursor.get("phase") or "nts_episode_breakdown"
        scene_index = int(cursor.get("scene_index") or 1)
        chapter_index = int(cursor.get("chapter_index") or 0)
        if not cursor.get("phase"):
            cursor["phase"] = phase

        source_snapshot_id = snapshot.id
        raw_source_snapshot_id = state.get("novel_source_snapshot_id")
        if raw_source_snapshot_id is None:
            existing_source = state.get("novel_source")
            if isinstance(existing_source, dict):
                raw_source_snapshot_id = existing_source.get("source_snapshot_id")
        if raw_source_snapshot_id is not None:
            try:
                source_snapshot_id = uuid.UUID(str(raw_source_snapshot_id))
            except (TypeError, ValueError):
                run.status = RunStatus.failed
                run.error = {"detail": "invalid_source_snapshot_id"}
                run.state = state
                await session.commit()
                return {"phase": phase, "detail": "invalid_source_snapshot_id"}

        source_snapshot = snapshot
        if source_snapshot_id != snapshot.id:
            source_snapshot = await session.get(BriefSnapshot, source_snapshot_id)
            if not source_snapshot:
                run.status = RunStatus.failed
                run.error = {"detail": "source_snapshot_not_found"}
                run.state = state
                await session.commit()
                return {"phase": phase, "detail": "source_snapshot_not_found"}
            if source_snapshot.brief_id != snapshot.brief_id:
                run.status = RunStatus.failed
                run.error = {"detail": "source_snapshot_not_in_same_brief"}
                run.state = state
                await session.commit()
                return {"phase": phase, "detail": "source_snapshot_not_in_same_brief"}

        output_spec = dict((brief_json.get("output_spec") or {}) if isinstance(brief_json, dict) else {})
        conversion_output_spec = state.get("conversion_output_spec")
        has_run_notes = False
        if isinstance(conversion_output_spec, dict):
            cleaned = dict(conversion_output_spec)
            if "script_format_notes" in cleaned:
                raw_notes = cleaned.get("script_format_notes")
                if raw_notes is None:
                    cleaned.pop("script_format_notes", None)
                else:
                    notes = str(raw_notes).strip()
                    if not notes:
                        cleaned.pop("script_format_notes", None)
                    else:
                        cleaned["script_format_notes"] = notes
                        has_run_notes = True
            output_spec = deep_merge(output_spec, cleaned)

        raw_existing_notes = output_spec.get("script_format_notes")
        if raw_existing_notes is None:
            output_spec.pop("script_format_notes", None)
        else:
            existing_notes = str(raw_existing_notes).strip()
            if existing_notes:
                output_spec["script_format_notes"] = existing_notes
            else:
                output_spec.pop("script_format_notes", None)

        if (not has_run_notes) and ("script_format_notes" not in output_spec):
            defaults = await get_novel_to_script_prompt_defaults(session=session)
            global_notes = defaults.get("conversion_notes")
            if isinstance(global_notes, str):
                global_notes = global_notes.strip()
                if global_notes:
                    output_spec["script_format_notes"] = global_notes
        brief_json_for_conversion = dict(brief_json) if isinstance(brief_json, dict) else {}
        brief_json_for_conversion["output_spec"] = output_spec

        if phase.startswith("nts_episode_"):
            sources = await _select_latest_novel_chapter_versions(
                session=session,
                brief_snapshot_id=source_snapshot.id,
            )
            if not sources:
                run.status = RunStatus.failed
                run.error = {"detail": "novel_source_missing"}
                run.state = state
                await session.commit()
                return {"phase": phase, "detail": "novel_source_missing"}

            digests: list[dict[str, Any]] = []
            source_version_ids: list[str] = []
            sources_by_ordinal: dict[int, tuple[Artifact, ArtifactVersion]] = {}
            for ordinal, artifact, version in sources:
                sources_by_ordinal[int(ordinal)] = (artifact, version)
                meta = dict(version.meta or {})
                fact_digest = str(meta.get("fact_digest") or "").strip()
                tone_digest = str(meta.get("tone_digest") or "").strip()
                chapter_title = str(
                    meta.get("chapter_title") or meta.get("title") or artifact.title or f"第{ordinal}章"
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

            state["novel_source"] = {
                "source_snapshot_id": str(source_snapshot.id),
                "artifact_version_ids": source_version_ids,
                "chapter_digests": digests,
            }

            ordinals = sorted(sources_by_ordinal.keys())
            if chapter_index <= 0:
                chapter_index = ordinals[0]
                cursor["chapter_index"] = chapter_index
            if chapter_index not in sources_by_ordinal:
                run.status = RunStatus.failed
                run.error = {"detail": "chapter_not_found", "chapter_index": chapter_index}
                run.state = state
                await session.commit()
                return {"phase": phase, "detail": "chapter_not_found"}

            chapter_artifact, chapter_version = sources_by_ordinal[int(chapter_index)]
            chapter_meta = dict(chapter_version.meta or {})
            chapter_title = str(
                chapter_meta.get("chapter_title")
                or chapter_meta.get("title")
                or chapter_artifact.title
                or f"第{chapter_index}章"
            )
            chapter_text = (chapter_version.content_text or "").strip()
            if len(chapter_text) > 20000:
                chapter_text = chapter_text[:20000].rstrip() + "\n\n（后续内容已截断）"

            prev_digests = (
                list(state.get("script_episode_digests") or []) if isinstance(state.get("script_episode_digests"), list) else []
            )
            prev_lines: list[str] = []
            for item in prev_digests[-3:]:
                idx = item.get("chapter_index") or item.get("episode_index") or item.get("index")
                title = item.get("chapter_title") or item.get("episode_title") or item.get("title") or ""
                fact = item.get("fact_digest") or ""
                if idx:
                    prefix = f"第{idx}集"
                    if title:
                        prefix += f"《{title}》"
                    prev_lines.append(f"{prefix}：{fact}".strip())
            prev_episode_digests_text = "\n".join([line for line in prev_lines if line]) or "(none)"

            episode_json = {
                "episode_index": int(chapter_index),
                "chapter_title": chapter_title,
                "output_spec": output_spec,
            }
            evidence_text = (
                f"【前情摘要】\n{prev_episode_digests_text}\n\n---\n\n【本章标题】{chapter_title}\n\n【本章全文】\n{chapter_text}"
            ).strip()

            if phase == "nts_episode_breakdown":
                raw = await _llm_complete_with_optional_stream(
                    llm=llm,
                    system_prompt=load_prompt("nts_episode_breakdown_system.md"),
                    user_prompt=render_prompt(
                        load_prompt("nts_episode_breakdown_user.md"),
                        {
                            "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                            "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                            "EPISODE_JSON": json.dumps(episode_json, ensure_ascii=False, indent=2),
                            "PREV_EPISODE_DIGESTS_TEXT": prev_episode_digests_text,
                            "CHAPTER_TEXT": chapter_text or "(empty)",
                        },
                    ),
                    hub=hub,
                    run_id=run.id,
                    step_id=step_id,
                    step_name="nts_episode_breakdown",
                )
                payload = extract_json_object(raw)
                breakdown = EpisodeBreakdown.model_validate(payload)
                state["episode_breakdown"] = breakdown.model_dump(mode="json")
                cursor["phase"] = "nts_episode_draft"
                cursor["chapter_index"] = int(chapter_index)
                state["fix_attempt"] = 0
                run.state = state
                await session.commit()
                return {"phase": phase, "episode_breakdown": state["episode_breakdown"]}

            if phase == "nts_episode_draft":
                breakdown_json = state.get("episode_breakdown") or {}
                raw = await _llm_complete_with_optional_stream(
                    llm=llm,
                    system_prompt=load_prompt("nts_episode_draft_system.md"),
                    user_prompt=render_prompt(
                        load_prompt("nts_episode_draft_user.md"),
                        {
                            "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                            "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                            "EPISODE_JSON": json.dumps(episode_json, ensure_ascii=False, indent=2),
                            "EPISODE_BREAKDOWN_JSON": json.dumps(
                                breakdown_json, ensure_ascii=False, indent=2
                            ),
                            "PREV_EPISODE_DIGESTS_TEXT": prev_episode_digests_text,
                            "CHAPTER_TEXT": chapter_text or "(empty)",
                        },
                    ),
                    hub=hub,
                    run_id=run.id,
                    step_id=step_id,
                    step_name="nts_episode_draft",
                )
                payload = extract_json_object(raw)
                draft = DraftResult.model_validate(payload)
                state["draft"] = {
                    "kind": "episode",
                    "index": int(chapter_index),
                    "title": draft.title,
                    "text": draft.text,
                }
                cursor["phase"] = "nts_episode_critic"
                run.state = state
                await session.commit()
                return {"phase": phase, "chapter_index": int(chapter_index), "draft_preview": draft.text[:500]}

            if phase == "nts_episode_critic":
                draft_state = state.get("draft") or {}
                draft_text = str(draft_state.get("text") or "")
                paragraphs, numbered = numbered_paragraphs(draft_text)

                script_format = str(output_spec.get("script_format") or "custom")
                format_issues = _nts_episode_format_issues(
                    text=draft_text, script_format=script_format, episode_index=int(chapter_index)
                )
                if format_issues:
                    rewrite_indices = list(range(1, len(paragraphs) + 1)) if paragraphs else []
                    critic = CriticResult(
                        hard_pass=False,
                        hard_errors=format_issues,
                        soft_scores={"format": 0},
                        rewrite_paragraph_indices=rewrite_indices,
                        rewrite_instructions=(
                            "格式修复：只输出这一集的剧本文本，不要包含任何提示词/规则/执行流程/STEP1/STEP2。"
                            f"本集为第{chapter_index}集，要求集头仅一次（例如“第{chapter_index}集…”或“第十二集…”这类中文数字写法），"
                            f"场号默认使用“{chapter_index}-1 / {chapter_index}-2 …”（也可用“{chapter_index}.1 / {chapter_index}.2 …”）。"
                            "删除重复的集头/错误的场号/重复的场景块，并确保场号递增不重复。"
                        ),
                        fact_digest="",
                        tone_digest="",
                        state_patch={},
                    )
                    state["critic"] = critic.model_dump(mode="json")

                    fix_attempt = int(state.get("fix_attempt") or 0)
                    if fix_attempt >= max_fix_attempts:
                        run.status = RunStatus.failed
                        run.error = {"detail": "max_fix_attempts_exceeded", "hard_errors": critic.hard_errors}
                        run.state = state
                        await session.commit()
                        return {
                            "phase": phase,
                            "hard_pass": False,
                            "hard_errors": critic.hard_errors,
                            "soft_scores": critic.soft_scores,
                            "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
                        }

                    cursor["phase"] = "nts_episode_fix"
                    run.state = state
                    await session.commit()
                    return {
                        "phase": phase,
                        "hard_pass": False,
                        "hard_errors": critic.hard_errors,
                        "soft_scores": critic.soft_scores,
                        "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
                    }

                raw = await _llm_complete_with_optional_stream(
                    llm=llm,
                    system_prompt=load_prompt("nts_critic_system.md"),
                    user_prompt=render_prompt(
                        load_prompt("nts_critic_user.md"),
                        {
                            "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                            "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                            "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                            "EVIDENCE_TEXT": evidence_text or "(none)",
                        },
                    ),
                    hub=hub,
                    run_id=run.id,
                    step_id=step_id,
                    step_name="nts_episode_critic",
                )
                payload = extract_json_object(raw)
                critic = CriticResult.model_validate(payload)
                if (not critic.hard_pass) and (not critic.rewrite_paragraph_indices) and paragraphs:
                    critic.rewrite_paragraph_indices = list(range(1, len(paragraphs) + 1))
                state["critic"] = critic.model_dump(mode="json")

                fix_attempt = int(state.get("fix_attempt") or 0)
                if not critic.hard_pass or critic.rewrite_paragraph_indices:
                    if fix_attempt >= max_fix_attempts:
                        run.status = RunStatus.failed
                        run.error = {"detail": "max_fix_attempts_exceeded", "hard_errors": critic.hard_errors}
                        run.state = state
                        await session.commit()
                        return {"phase": phase, "hard_pass": False, "hard_errors": critic.hard_errors}
                    cursor["phase"] = "nts_episode_fix"
                else:
                    cursor["phase"] = "nts_episode_commit"

                run.state = state
                await session.commit()
                return {
                    "phase": phase,
                    "hard_pass": critic.hard_pass,
                    "hard_errors": critic.hard_errors,
                    "soft_scores": critic.soft_scores,
                    "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
                }

            if phase == "nts_episode_fix":
                critic_json = state.get("critic") or {}
                critic = CriticResult.model_validate(critic_json)
                draft_state = state.get("draft") or {}
                draft_text = str(draft_state.get("text") or "")
                paragraphs, numbered = numbered_paragraphs(draft_text)

                raw = await _llm_complete_with_optional_stream(
                    llm=llm,
                    system_prompt=load_prompt("rewrite_system.md"),
                    user_prompt=render_prompt(
                        load_prompt("nts_episode_rewrite_user.md"),
                        {
                            "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                            "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                            "EPISODE_JSON": json.dumps(episode_json, ensure_ascii=False, indent=2),
                            "EVIDENCE_TEXT": evidence_text or "(none)",
                            "REWRITE_INSTRUCTIONS": critic.rewrite_instructions or "提升一致性与质量",
                            "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                            "REWRITE_PARAGRAPH_INDICES_JSON": json.dumps(
                                critic.rewrite_paragraph_indices, ensure_ascii=False
                            ),
                        },
                    ),
                    hub=hub,
                    run_id=run.id,
                    step_id=step_id,
                    step_name="nts_episode_fix",
                )
                payload = extract_json_object(raw)
                rewrite = RewriteResult.model_validate(payload)
                replacements = {int(k): v for k, v in rewrite.replacements.items()}
                updated_paragraphs = apply_replacements(paragraphs, replacements)
                new_text = join_paragraphs(updated_paragraphs)
                state["draft"] = {
                    "kind": "episode",
                    "index": int(chapter_index),
                    "title": draft_state.get("title"),
                    "text": new_text,
                }
                state.pop("critic", None)
                state["fix_attempt"] = int(state.get("fix_attempt") or 0) + 1
                cursor["phase"] = "nts_episode_critic"
                run.state = state
                await session.commit()
                return {"phase": phase, "updated_preview": new_text[:500]}

            if phase == "nts_episode_commit":
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
                explicit_title = draft_state.get("title")
                episode_title = (
                    str(explicit_title).strip()
                    if isinstance(explicit_title, str) and str(explicit_title).strip()
                    else None
                )
                if episode_title is None:
                    episode_title = _extract_episode_title(text=draft_text, episode_index=int(chapter_index))
                if episode_title is None:
                    episode_title = chapter_title

                artifact = await _get_or_create_artifact(
                    session=session,
                    kind=ArtifactKind.script_scene,
                    ordinal=int(chapter_index),
                    title=episode_title,
                )
                version = ArtifactVersion(
                    artifact_id=artifact.id,
                    source=ArtifactVersionSource.agent,
                    content_text=draft_text,
                    meta={
                        "fact_digest": critic.fact_digest,
                        "tone_digest": critic.tone_digest,
                        "soft_scores": critic.soft_scores,
                        "episode_index": int(chapter_index),
                        "episode_title": episode_title,
                        "chapter_title": chapter_title,
                        "source_kind": "novel_to_script",
                    },
                    workflow_run_id=run.id,
                    brief_snapshot_id=snapshot.id,
                )
                session.add(version)
                await session.commit()
                await session.refresh(version)

                if not _rag_is_disabled(state):
                    try:
                        await index_artifact_version(
                            session=session,
                            embeddings=embeddings,
                            brief_snapshot_id=snapshot.id,
                            artifact_version_id=version.id,
                            content_text=draft_text,
                            meta={"kind": "script_scene", "ordinal": int(chapter_index)},
                        )
                    except Exception as exc:
                        await session.rollback()
                        _record_embeddings_error(state=state, where="nts_episode_commit:index_artifact_version", exc=exc)

                current_state = deep_merge(current_state, critic.state_patch)
                state["current_state"] = current_state
                state.pop("draft", None)
                state.pop("critic", None)
                state.pop("episode_breakdown", None)
                state["fix_attempt"] = 0

                episode_digests = (
                    list(state.get("script_episode_digests") or [])
                    if isinstance(state.get("script_episode_digests"), list)
                    else []
                )
                episode_digests.append(
                    {
                        "chapter_index": int(chapter_index),
                        "chapter_title": episode_title,
                        "fact_digest": critic.fact_digest,
                        "tone_digest": critic.tone_digest,
                    }
                )
                state["script_episode_digests"] = episode_digests

                current_pos = ordinals.index(int(chapter_index))
                next_pos = current_pos + 1
                if next_pos >= len(ordinals):
                    run.status = RunStatus.succeeded
                    cursor["phase"] = "done"
                else:
                    cursor["chapter_index"] = ordinals[next_pos]
                    cursor["phase"] = "nts_episode_breakdown"

                run.state = state
                await session.commit()
                return {
                    "phase": phase,
                    "artifact_id": str(artifact.id),
                    "artifact_version_id": str(version.id),
                    "fact_digest": critic.fact_digest,
                    "tone_digest": critic.tone_digest,
                }

        if phase == "nts_scene_list":
            sources = await _select_latest_novel_chapter_versions(
                session=session,
                brief_snapshot_id=source_snapshot.id,
            )
            if not sources:
                run.status = RunStatus.failed
                run.error = {"detail": "novel_source_missing"}
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

            state["novel_source"] = {
                "source_snapshot_id": str(source_snapshot.id),
                "artifact_version_ids": source_version_ids,
                "chapter_digests": digests,
            }

            raw = await _llm_complete_with_optional_stream(
                llm=llm,
                system_prompt=load_prompt("nts_scene_list_system.md"),
                user_prompt=render_prompt(
                    load_prompt("nts_scene_list_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                        "NOVEL_CHAPTER_DIGESTS_JSON": json.dumps(
                            digests, ensure_ascii=False, indent=2
                        ),
                    },
                ),
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="nts_scene_list",
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
            query = f"NTS Scene {scene.slug} {scene.title} {scene.location} {scene.time} {' '.join(scene.characters)} {scene.purpose}"
            evidence_chunks = []
            if not _rag_is_disabled(state):
                try:
                    evidence_chunks = await retrieve_evidence(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=source_snapshot.id,
                        query=query,
                        limit=8,
                    )
                except Exception as exc:
                    _record_embeddings_error(state=state, where="nts_scene_draft:retrieve_evidence", exc=exc)
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            if digest_lines:
                evidence_text = (digest_lines + ("\n\n---\n\n" + evidence_text if evidence_text else "")).strip()

            raw = await _llm_complete_with_optional_stream(
                llm=llm,
                system_prompt=load_prompt("nts_scene_draft_system.md"),
                user_prompt=render_prompt(
                    load_prompt("nts_scene_draft_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "SCENE_JSON": json.dumps(
                            deep_merge(
                                scene.model_dump(mode="json"),
                                {
                                    "output_spec": output_spec,
                                    "generation_context": {
                                        "scene_total": len(scene_list.scenes),
                                        "is_first_scene": scene_index == 1,
                                        "is_last_scene": scene_index == len(scene_list.scenes),
                                    },
                                },
                            ),
                            ensure_ascii=False,
                            indent=2,
                        ),
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="nts_scene_draft",
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

            script_format = str(output_spec.get("script_format") or "custom")
            format_issues = _nts_scene_format_issues(text=draft_text, script_format=script_format)
            if format_issues:
                rewrite_indices = list(range(1, len(paragraphs) + 1)) if paragraphs else []
                critic = CriticResult(
                    hard_pass=False,
                    hard_errors=format_issues,
                    soft_scores={"format": 0},
                    rewrite_paragraph_indices=rewrite_indices,
                    rewrite_instructions=(
                        "格式修复：只输出一个场景的剧本正文，不要包含任何提示词/规则/执行流程/STEP1/STEP2。"
                        f"本场是 {scene.slug}《{scene.title}》，地点：{scene.location}，时间：{scene.time}，人物：{', '.join(scene.characters) or '（无）'}。"
                        "如果草稿里出现了多个场景编号（例如 1-1/1-2…）或多个 INT./EXT. 标题，只保留与本场相关的一个，删除其余。"
                    ),
                    fact_digest="",
                    tone_digest="",
                    state_patch={},
                )
                state["critic"] = critic.model_dump(mode="json")

                fix_attempt = int(state.get("fix_attempt") or 0)
                if fix_attempt >= max_fix_attempts:
                    run.status = RunStatus.failed
                    run.error = {"detail": "max_fix_attempts_exceeded", "hard_errors": critic.hard_errors}
                    run.state = state
                    await session.commit()
                    return {
                        "phase": phase,
                        "hard_pass": False,
                        "hard_errors": critic.hard_errors,
                        "soft_scores": critic.soft_scores,
                        "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
                    }

                cursor["phase"] = "nts_scene_fix"
                run.state = state
                await session.commit()
                return {
                    "phase": phase,
                    "hard_pass": False,
                    "hard_errors": critic.hard_errors,
                    "soft_scores": critic.soft_scores,
                    "rewrite_paragraph_indices": critic.rewrite_paragraph_indices,
                }

            query = f"NTS Critic {scene.slug} {scene.title}"
            evidence_chunks = []
            if not _rag_is_disabled(state):
                try:
                    evidence_chunks = await retrieve_evidence(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=source_snapshot.id,
                        query=query,
                        limit=8,
                    )
                except Exception as exc:
                    _record_embeddings_error(state=state, where="nts_scene_critic:retrieve_evidence", exc=exc)
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            if digest_lines:
                evidence_text = (digest_lines + ("\n\n---\n\n" + evidence_text if evidence_text else "")).strip()

            raw = await _llm_complete_with_optional_stream(
                llm=llm,
                system_prompt=load_prompt("nts_critic_system.md"),
                user_prompt=render_prompt(
                    load_prompt("nts_critic_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                    },
                ),
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="nts_scene_critic",
            )
            payload = extract_json_object(raw)
            critic = CriticResult.model_validate(payload)
            if (not critic.hard_pass) and (not critic.rewrite_paragraph_indices) and paragraphs:
                critic.rewrite_paragraph_indices = list(range(1, len(paragraphs) + 1))
            state["critic"] = critic.model_dump(mode="json")

            fix_attempt = int(state.get("fix_attempt") or 0)
            if not critic.hard_pass or critic.rewrite_paragraph_indices:
                if fix_attempt >= max_fix_attempts:
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

            if "format_multiple_scene_blocks" in set(critic.hard_errors):
                extracted = _nts_extract_custom_scene_block(text=draft_text, slug=scene.slug)
                if extracted is not None:
                    state["draft"] = {
                        "kind": "scene",
                        "index": scene.index,
                        "slug": scene.slug,
                        "text": extracted,
                    }
                    state.pop("critic", None)
                    state["fix_attempt"] = int(state.get("fix_attempt") or 0) + 1
                    cursor["phase"] = "nts_scene_critic"
                    run.state = state
                    await session.commit()
                    return {
                        "phase": phase,
                        "auto_format_fix_applied": True,
                        "updated_preview": extracted[:500],
                    }

            query = f"NTS Fix {scene.slug} {scene.title}"
            evidence_chunks = []
            if not _rag_is_disabled(state):
                try:
                    evidence_chunks = await retrieve_evidence(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=source_snapshot.id,
                        query=query,
                        limit=8,
                    )
                except Exception as exc:
                    _record_embeddings_error(state=state, where="nts_scene_fix:retrieve_evidence", exc=exc)
            evidence_text = "\n\n---\n\n".join([c.content_text for c in evidence_chunks])
            if digest_lines:
                evidence_text = (digest_lines + ("\n\n---\n\n" + evidence_text if evidence_text else "")).strip()

            raw = await _llm_complete_with_optional_stream(
                llm=llm,
                system_prompt=load_prompt("rewrite_system.md"),
                user_prompt=render_prompt(
                    load_prompt("nts_rewrite_user.md"),
                    {
                        "BRIEF_JSON": json.dumps(brief_json_for_conversion, ensure_ascii=False, indent=2),
                        "CURRENT_STATE_JSON": json.dumps(current_state, ensure_ascii=False, indent=2),
                        "SCENE_JSON": json.dumps(
                            deep_merge(scene.model_dump(mode="json"), {"output_spec": output_spec}),
                            ensure_ascii=False,
                            indent=2,
                        ),
                        "EVIDENCE_TEXT": evidence_text or "(none)",
                        "REWRITE_INSTRUCTIONS": critic.rewrite_instructions or "提升一致性与质量",
                        "NUMBERED_PARAGRAPHS": numbered or "(empty)",
                        "REWRITE_PARAGRAPH_INDICES_JSON": json.dumps(
                            critic.rewrite_paragraph_indices, ensure_ascii=False
                        ),
                    },
                ),
                hub=hub,
                run_id=run.id,
                step_id=step_id,
                step_name="nts_scene_fix",
            )
            payload = extract_json_object(raw)
            rewrite = RewriteResult.model_validate(payload)
            replacements = {int(k): v for k, v in rewrite.replacements.items()}
            updated_paragraphs = apply_replacements(paragraphs, replacements)
            new_text = join_paragraphs(updated_paragraphs)
            state["draft"] = {"kind": "scene", "index": scene.index, "slug": scene.slug, "text": new_text}
            state.pop("critic", None)
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

            if not _rag_is_disabled(state):
                try:
                    await index_artifact_version(
                        session=session,
                        embeddings=embeddings,
                        brief_snapshot_id=snapshot.id,
                        artifact_version_id=version.id,
                        content_text=draft_text,
                        meta={"kind": "script_scene", "ordinal": scene.index},
                    )
                except Exception as exc:
                    await session.rollback()
                    _record_embeddings_error(state=state, where="nts_scene_commit:index_artifact_version", exc=exc)

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
        outputs = await execute_next_step(
            session=session, llm=llm, embeddings=embeddings, run=run, hub=None, step_id=step_run.id
        )
        step_run.status = RunStatus.succeeded
        step_run.outputs = outputs
        step_run.finished_at = _now()
        await session.commit()
        await session.refresh(step_run)
        return step_run
    except (ValidationError, RuntimeError) as exc:
        error_chain = format_exception_chain(exc)
        step_run.status = RunStatus.failed
        step_run.error = error_chain
        step_run.finished_at = _now()
        run.status = RunStatus.failed
        run.error = {
            "detail": "step_failed",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
            "error_chain": error_chain,
        }
        await session.commit()
        await session.refresh(step_run)
        return step_run
