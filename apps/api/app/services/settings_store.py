from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import AppSetting
from app.schemas.briefs import ScriptFormat
from app.services.json_utils import deep_merge

OUTPUT_SPEC_DEFAULTS_KEY = "output_spec_defaults"
LLM_PROVIDER_SETTINGS_KEY = "llm_provider_settings"

SERVER_OUTPUT_SPEC_DEFAULTS: dict[str, Any] = {
    "language": "zh-CN",
    "script_format": ScriptFormat.screenplay_int_ext.value,
    "script_format_notes": None,
    "max_fix_attempts": 2,
}


def _normalize_optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    return cleaned or None


async def get_output_spec_defaults(*, session: AsyncSession) -> dict[str, Any]:
    setting = await session.get(AppSetting, OUTPUT_SPEC_DEFAULTS_KEY)
    stored = dict(setting.value or {}) if setting else {}
    resolved = deep_merge(SERVER_OUTPUT_SPEC_DEFAULTS, stored)

    if not resolved.get("language"):
        resolved["language"] = SERVER_OUTPUT_SPEC_DEFAULTS["language"]
    if not resolved.get("script_format"):
        resolved["script_format"] = SERVER_OUTPUT_SPEC_DEFAULTS["script_format"]

    raw_max_fix = resolved.get("max_fix_attempts")
    try:
        max_fix_attempts = int(raw_max_fix)
    except (TypeError, ValueError):
        max_fix_attempts = int(SERVER_OUTPUT_SPEC_DEFAULTS["max_fix_attempts"])
    if max_fix_attempts < 0:
        max_fix_attempts = 0
    resolved["max_fix_attempts"] = max_fix_attempts

    return resolved


async def patch_output_spec_defaults(
    *,
    session: AsyncSession,
    patch: dict[str, Any],
) -> dict[str, Any]:
    setting = await session.get(AppSetting, OUTPUT_SPEC_DEFAULTS_KEY)
    stored: dict[str, Any] = dict(setting.value or {}) if setting else {}

    for key, value in patch.items():
        if value is None:
            stored.pop(key, None)
        elif isinstance(value, ScriptFormat):
            stored[key] = value.value
        else:
            stored[key] = value

    if setting is None:
        setting = AppSetting(key=OUTPUT_SPEC_DEFAULTS_KEY, value=stored)
        session.add(setting)
    else:
        setting.value = stored

    await session.commit()
    return await get_output_spec_defaults(session=session)


async def get_llm_provider_settings_raw(*, session: AsyncSession) -> dict[str, Any]:
    setting = await session.get(AppSetting, LLM_PROVIDER_SETTINGS_KEY)
    return dict(setting.value or {}) if setting else {}


def resolve_llm_provider_effective_config(
    *,
    stored: dict[str, Any],
    env_settings: Settings,
) -> dict[str, Any]:
    stored_base_url = _normalize_optional_str(stored.get("base_url"))
    stored_model = _normalize_optional_str(stored.get("model"))
    stored_embeddings_model = _normalize_optional_str(stored.get("embeddings_model"))

    base_url = stored_base_url or env_settings.resolved_openai_base_url()
    model = stored_model or env_settings.openai_model
    embeddings_model = stored_embeddings_model or env_settings.openai_embeddings_model

    timeout_raw = stored.get("timeout_s")
    try:
        timeout_s = float(timeout_raw) if timeout_raw is not None else float(env_settings.openai_timeout_s)
    except (TypeError, ValueError):
        timeout_s = float(env_settings.openai_timeout_s)

    max_retries_raw = stored.get("max_retries")
    try:
        max_retries = int(max_retries_raw) if max_retries_raw is not None else int(env_settings.openai_max_retries)
    except (TypeError, ValueError):
        max_retries = int(env_settings.openai_max_retries)
    if max_retries < 0:
        max_retries = 0

    api_key = _normalize_optional_str(stored.get("api_key")) or (
        _normalize_optional_str(env_settings.openai_api_key) if env_settings.openai_api_key else None
    )

    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "embeddings_model": embeddings_model,
        "timeout_s": timeout_s,
        "max_retries": max_retries,
    }


async def get_llm_provider_settings(
    *,
    session: AsyncSession,
    env_settings: Settings,
) -> dict[str, Any]:
    stored = await get_llm_provider_settings_raw(session=session)
    effective = resolve_llm_provider_effective_config(stored=stored, env_settings=env_settings)
    api_key_configured = bool(_normalize_optional_str(stored.get("api_key")))

    return {
        "base_url": effective.get("base_url"),
        "model": effective.get("model"),
        "embeddings_model": effective.get("embeddings_model"),
        "timeout_s": effective.get("timeout_s"),
        "max_retries": effective.get("max_retries"),
        "api_key_configured": api_key_configured,
    }


async def patch_llm_provider_settings(
    *,
    session: AsyncSession,
    patch: dict[str, Any],
) -> None:
    setting = await session.get(AppSetting, LLM_PROVIDER_SETTINGS_KEY)
    stored: dict[str, Any] = dict(setting.value or {}) if setting else {}

    for key, value in patch.items():
        if key == "api_key":
            if value is None:
                stored.pop("api_key", None)
            else:
                cleaned = _normalize_optional_str(value)
                if cleaned is None:
                    stored.pop("api_key", None)
                else:
                    stored["api_key"] = cleaned
            continue

        if value is None:
            stored.pop(key, None)
            continue

        if key in {"base_url", "model", "embeddings_model"}:
            cleaned = _normalize_optional_str(value)
            if cleaned is None:
                stored.pop(key, None)
            else:
                stored[key] = cleaned
        elif key == "timeout_s":
            stored[key] = float(value)
        elif key == "max_retries":
            stored[key] = int(value)
        else:
            stored[key] = value

    if setting is None:
        setting = AppSetting(key=LLM_PROVIDER_SETTINGS_KEY, value=stored)
        session.add(setting)
    else:
        setting.value = stored

    await session.commit()
