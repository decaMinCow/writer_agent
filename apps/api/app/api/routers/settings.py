from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.settings import OutputSpecDefaultsPatch, OutputSpecDefaultsRead
from app.services.settings_store import get_output_spec_defaults, patch_output_spec_defaults

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/output-spec", response_model=OutputSpecDefaultsRead)
async def get_output_spec_defaults_route(
    session: AsyncSession = Depends(get_db_session),
) -> OutputSpecDefaultsRead:
    resolved = await get_output_spec_defaults(session=session)
    return OutputSpecDefaultsRead.model_validate(resolved)


@router.patch("/output-spec", response_model=OutputSpecDefaultsRead)
async def patch_output_spec_defaults_route(
    payload: OutputSpecDefaultsPatch,
    session: AsyncSession = Depends(get_db_session),
) -> OutputSpecDefaultsRead:
    patch: dict[str, object | None] = {}
    if "language" in payload.model_fields_set:
        patch["language"] = payload.language
    if "script_format" in payload.model_fields_set:
        patch["script_format"] = payload.script_format
    if "script_format_notes" in payload.model_fields_set:
        patch["script_format_notes"] = payload.script_format_notes

    resolved = await patch_output_spec_defaults(session=session, patch=patch)
    return OutputSpecDefaultsRead.model_validate(resolved)

