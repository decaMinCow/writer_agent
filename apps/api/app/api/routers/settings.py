from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.settings import (
    LlmProviderSettingsPatch,
    LlmProviderSettingsRead,
    NovelToScriptPromptDefaultsPatch,
    NovelToScriptPromptDefaultsRead,
    OutputSpecDefaultsPatch,
    OutputSpecDefaultsRead,
)
from app.services.settings_store import (
    get_llm_provider_settings,
    get_novel_to_script_prompt_defaults,
    get_output_spec_defaults,
    patch_llm_provider_settings,
    patch_novel_to_script_prompt_defaults,
    patch_output_spec_defaults,
 )

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
    if "max_fix_attempts" in payload.model_fields_set:
        patch["max_fix_attempts"] = payload.max_fix_attempts
    if "auto_step_retries" in payload.model_fields_set:
        patch["auto_step_retries"] = payload.auto_step_retries
    if "auto_step_backoff_s" in payload.model_fields_set:
        patch["auto_step_backoff_s"] = payload.auto_step_backoff_s

    resolved = await patch_output_spec_defaults(session=session, patch=patch)
    return OutputSpecDefaultsRead.model_validate(resolved)


@router.get("/novel-to-script-prompt", response_model=NovelToScriptPromptDefaultsRead)
async def get_novel_to_script_prompt_defaults_route(
    session: AsyncSession = Depends(get_db_session),
) -> NovelToScriptPromptDefaultsRead:
    resolved = await get_novel_to_script_prompt_defaults(session=session)
    return NovelToScriptPromptDefaultsRead.model_validate(resolved)


@router.patch("/novel-to-script-prompt", response_model=NovelToScriptPromptDefaultsRead)
async def patch_novel_to_script_prompt_defaults_route(
    payload: NovelToScriptPromptDefaultsPatch,
    session: AsyncSession = Depends(get_db_session),
) -> NovelToScriptPromptDefaultsRead:
    patch: dict[str, object | None] = {}
    if "conversion_notes" in payload.model_fields_set:
        patch["conversion_notes"] = payload.conversion_notes
    resolved = await patch_novel_to_script_prompt_defaults(session=session, patch=patch)
    return NovelToScriptPromptDefaultsRead.model_validate(resolved)


@router.get("/llm-provider", response_model=LlmProviderSettingsRead)
async def get_llm_provider_settings_route(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> LlmProviderSettingsRead:
    env_settings = getattr(request.app.state, "settings", None)
    resolved = await get_llm_provider_settings(session=session, env_settings=env_settings)
    return LlmProviderSettingsRead.model_validate(resolved)


@router.patch("/llm-provider", response_model=LlmProviderSettingsRead)
async def patch_llm_provider_settings_route(
    request: Request,
    payload: LlmProviderSettingsPatch,
    session: AsyncSession = Depends(get_db_session),
) -> LlmProviderSettingsRead:
    patch: dict[str, object | None] = {}
    if "base_url" in payload.model_fields_set:
        patch["base_url"] = payload.base_url
    if "model" in payload.model_fields_set:
        patch["model"] = payload.model
    if "embeddings_model" in payload.model_fields_set:
        patch["embeddings_model"] = payload.embeddings_model
    if "timeout_s" in payload.model_fields_set:
        patch["timeout_s"] = payload.timeout_s
    if "max_retries" in payload.model_fields_set:
        patch["max_retries"] = payload.max_retries
    if "api_key" in payload.model_fields_set:
        patch["api_key"] = payload.api_key

    await patch_llm_provider_settings(session=session, patch=patch)
    env_settings = getattr(request.app.state, "settings", None)
    resolved = await get_llm_provider_settings(session=session, env_settings=env_settings)
    return LlmProviderSettingsRead.model_validate(resolved)
