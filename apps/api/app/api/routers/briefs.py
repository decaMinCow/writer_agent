from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

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
from app.services import cascade_delete
from app.services.brief_builder import build_brief_result, parse_brief_builder_output
from app.services.llm_provider import resolve_llm_client
from app.services.prompting import load_prompt, render_prompt
from app.services.settings_store import get_output_spec_defaults
from app.services.workflow_events import format_sse_event

router = APIRouter(prefix="/api/briefs", tags=["briefs"])


def _merge_named_items(base_list: list[Any], patch_list: list[Any]) -> list[Any]:
    if not patch_list:
        return list(patch_list)

    def name_of(item: Any) -> str | None:
        if not isinstance(item, dict):
            return None
        candidates = [
            item.get("name"),
            item.get("姓名"),
            item.get("名字"),
            item.get("角色名"),
        ]
        for raw in candidates:
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        return None

    patch_by_name: dict[str, dict[str, Any]] = {}
    patch_order: list[str] = []
    deletions: set[str] = set()
    for item in patch_list:
        name = name_of(item)
        if name is None:
            return list(patch_list)
        if bool(item.get("__delete__")):
            deletions.add(name)
            continue
        if name not in patch_by_name:
            patch_order.append(name)
        patch_by_name[name] = item

    merged_list: list[Any] = []
    seen: set[str] = set()
    for item in base_list:
        name = name_of(item)
        if name is None:
            merged_list.append(item)
            continue
        if name in deletions:
            seen.add(name)
            continue
        patch_item = patch_by_name.get(name)
        if patch_item is not None and isinstance(item, dict):
            merged_list.append(_deep_merge(item, patch_item, path=()))
            seen.add(name)
        else:
            merged_list.append(item)
            seen.add(name)

    for name in patch_order:
        if name in seen:
            continue
        merged_list.append(patch_by_name[name])

    return merged_list


def _deep_merge(base: dict[str, Any], patch: dict[str, Any], *, path: tuple[str, ...] = ()) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in patch.items():
        next_path = path + (key,)
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value, path=next_path)
        elif (
            isinstance(value, list)
            and isinstance(merged.get(key), list)
            and "characters" in next_path
        ):
            merged[key] = _merge_named_items(list(merged.get(key) or []), list(value))
        else:
            merged[key] = value
    return merged


def _extract_assistant_message_partial(raw: str) -> str | None:
    marker = '"assistant_message"'
    idx = raw.find(marker)
    if idx == -1:
        return None

    colon = raw.find(":", idx + len(marker))
    if colon == -1:
        return None

    i = colon + 1
    while i < len(raw) and raw[i].isspace():
        i += 1
    if i >= len(raw) or raw[i] != '"':
        return None

    # Parse JSON string value, best-effort (supports partial input).
    i += 1
    out: list[str] = []
    while i < len(raw):
        ch = raw[i]
        if ch == '"':
            break
        if ch == "\\":
            if i + 1 >= len(raw):
                break
            esc = raw[i + 1]
            if esc == '"':
                out.append('"')
                i += 2
                continue
            if esc == "\\":
                out.append("\\")
                i += 2
                continue
            if esc == "/":
                out.append("/")
                i += 2
                continue
            if esc == "b":
                out.append("\b")
                i += 2
                continue
            if esc == "f":
                out.append("\f")
                i += 2
                continue
            if esc == "n":
                out.append("\n")
                i += 2
                continue
            if esc == "r":
                out.append("\r")
                i += 2
                continue
            if esc == "t":
                out.append("\t")
                i += 2
                continue
            if esc == "u":
                if i + 6 > len(raw):
                    break
                hex_part = raw[i + 2 : i + 6]
                if all(c in "0123456789abcdefABCDEF" for c in hex_part):
                    out.append(chr(int(hex_part, 16)))
                    i += 6
                    continue
                break
            # Unknown escape; stop rather than emit garbage.
            break
        out.append(ch)
        i += 1

    return "".join(out)


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


@router.delete("/{brief_id}")
async def delete_brief(
    brief_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    brief = await session.get(Brief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="brief_not_found")

    await cascade_delete.delete_brief(session=session, brief_id=brief.id, app=request.app)
    return {"deleted": True}


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

    llm = await resolve_llm_client(session=session, app=request.app)
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


@router.post("/{brief_id}/messages/stream")
async def add_brief_message_stream(
    brief_id: uuid.UUID,
    payload: BriefMessageCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
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

    llm = await resolve_llm_client(session=session, app=request.app)
    if llm is None:
        raise HTTPException(status_code=400, detail="openai_not_configured")

    current_brief_json: dict[str, Any] = {"title": brief.title, "content": brief.content}
    system_prompt = load_prompt("brief_builder_system.md")
    user_prompt = render_prompt(
        load_prompt("brief_builder_user.md"),
        {
            "CURRENT_BRIEF_JSON": json.dumps(current_brief_json, ensure_ascii=False, indent=2),
            "MODE": payload.mode.value,
            "USER_MESSAGE": payload.content_text,
        },
    )

    async def event_stream():
        raw_output = ""
        streamed_assistant = ""
        try:
            # Flush an initial SSE frame quickly so the client can show "thinking..." state.
            yield format_sse_event(name="status", payload={"state": "started"})

            if hasattr(llm, "stream_complete"):
                async for delta in llm.stream_complete(
                    system_prompt=system_prompt, user_prompt=user_prompt
                ):
                    raw_output += delta
                    partial = _extract_assistant_message_partial(raw_output) or ""
                    if len(partial) > len(streamed_assistant):
                        append = partial[len(streamed_assistant) :]
                        streamed_assistant = partial
                        if append:
                            yield format_sse_event(name="assistant_delta", payload={"append": append})

                result = await parse_brief_builder_output(
                    llm=llm,
                    raw_output=raw_output,
                    max_attempts=2,
                )
            else:
                result = await build_brief_result(
                    llm=llm,
                    current_brief_json=current_brief_json,
                    mode=payload.mode,
                    user_message=payload.content_text,
                )

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

            payload_final = BriefMessageCreateResponse(
                brief=BriefRead.model_validate(brief),
                gap_report=result.gap_report,
                messages=messages,
            ).model_dump(mode="json")
            yield format_sse_event(name="final", payload=payload_final)
        except Exception as exc:
            yield format_sse_event(name="error", payload={"detail": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"cache-control": "no-cache", "x-accel-buffering": "no"},
    )
