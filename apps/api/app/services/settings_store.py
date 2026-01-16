from __future__ import annotations

import copy
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import AppSetting
from app.schemas.briefs import ScriptFormat
from app.services.json_utils import deep_merge

OUTPUT_SPEC_DEFAULTS_KEY = "output_spec_defaults"
LLM_PROVIDER_SETTINGS_KEY = "llm_provider_settings"
NOVEL_TO_SCRIPT_PROMPT_DEFAULTS_KEY = "novel_to_script_prompt_defaults"
PROMPT_PRESETS_KEY = "prompt_presets"

SERVER_OUTPUT_SPEC_DEFAULTS: dict[str, Any] = {
    "language": "zh-CN",
    "script_format": ScriptFormat.screenplay_int_ext.value,
    "script_format_notes": None,
    "max_fix_attempts": 2,
    "auto_step_retries": 3,
    "auto_step_backoff_s": 1.0,
}

SERVER_PROMPT_PRESETS_DEFAULTS: dict[str, Any] = {
    "script": {
        "default_preset_id": "default",
        "presets": [
            {"id": "default", "name": "默认", "text": ""},
        ],
    },
    "novel_to_script": {
        "default_preset_id": "default",
        "presets": [
            {"id": "default", "name": "默认", "text": ""},
        ],
    },
}


def _normalize_optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    return cleaned or None


def _normalize_prompt_preset_catalog(*, raw: object) -> dict[str, Any]:
    catalog: dict[str, Any] = raw if isinstance(raw, dict) else {}

    raw_presets = catalog.get("presets")
    presets_list: list[dict[str, Any]] = []
    if isinstance(raw_presets, list):
        seen_ids: set[str] = set()
        for item in raw_presets:
            if not isinstance(item, dict):
                continue
            preset_id = _normalize_optional_str(item.get("id"))
            if preset_id is None or preset_id in seen_ids:
                continue
            seen_ids.add(preset_id)
            preset_name = _normalize_optional_str(item.get("name")) or preset_id
            preset_text = item.get("text")
            if preset_text is None:
                preset_text = ""
            if not isinstance(preset_text, str):
                preset_text = str(preset_text)
            presets_list.append(
                {
                    "id": preset_id,
                    "name": preset_name,
                    "text": preset_text,
                }
            )

    default_preset_id = _normalize_optional_str(catalog.get("default_preset_id"))
    if not presets_list:
        return {"default_preset_id": None, "presets": []}

    preset_ids = {preset["id"] for preset in presets_list}
    if default_preset_id not in preset_ids:
        default_preset_id = presets_list[0]["id"]

    return {"default_preset_id": default_preset_id, "presets": presets_list}


def _normalize_prompt_presets(*, raw: dict[str, Any]) -> dict[str, Any]:
    merged = deep_merge(SERVER_PROMPT_PRESETS_DEFAULTS, raw)
    return {
        "script": _normalize_prompt_preset_catalog(raw=merged.get("script")),
        "novel_to_script": _normalize_prompt_preset_catalog(raw=merged.get("novel_to_script")),
    }


async def get_prompt_presets(*, session: AsyncSession) -> dict[str, Any]:
    setting = await session.get(AppSetting, PROMPT_PRESETS_KEY)
    if setting is not None:
        stored = dict(setting.value or {})
        return _normalize_prompt_presets(raw=stored)

    seeded = copy.deepcopy(SERVER_PROMPT_PRESETS_DEFAULTS)
    legacy_output_spec = await session.get(AppSetting, OUTPUT_SPEC_DEFAULTS_KEY)
    if legacy_output_spec is not None and isinstance(legacy_output_spec.value, dict):
        legacy_notes = _normalize_optional_str(legacy_output_spec.value.get("script_format_notes"))
        if legacy_notes is not None:
            seeded["script"]["presets"][0]["text"] = legacy_notes

    legacy_nts = await session.get(AppSetting, NOVEL_TO_SCRIPT_PROMPT_DEFAULTS_KEY)
    if legacy_nts is not None and isinstance(legacy_nts.value, dict):
        legacy_notes = _normalize_optional_str(legacy_nts.value.get("conversion_notes"))
        if legacy_notes is not None:
            seeded["novel_to_script"]["presets"][0]["text"] = legacy_notes

    normalized = _normalize_prompt_presets(raw=seeded)
    session.add(AppSetting(key=PROMPT_PRESETS_KEY, value=normalized))
    await session.commit()
    return normalized


async def patch_prompt_presets(
    *,
    session: AsyncSession,
    patch: dict[str, Any],
) -> dict[str, Any]:
    setting = await session.get(AppSetting, PROMPT_PRESETS_KEY)
    stored: dict[str, Any] = dict(setting.value or {}) if setting else {}

    for top_key, top_value in patch.items():
        if top_value is None:
            stored.pop(top_key, None)
            continue
        if not isinstance(top_value, dict):
            continue

        existing_catalog = stored.get(top_key)
        catalog: dict[str, Any] = dict(existing_catalog) if isinstance(existing_catalog, dict) else {}
        for key, value in top_value.items():
            if value is None:
                catalog.pop(key, None)
            else:
                catalog[key] = value
        stored[top_key] = catalog

    normalized = _normalize_prompt_presets(raw=stored)

    if setting is None:
        setting = AppSetting(key=PROMPT_PRESETS_KEY, value=normalized)
        session.add(setting)
    else:
        setting.value = normalized

    await session.commit()
    return normalized


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

    raw_retries = resolved.get("auto_step_retries")
    try:
        auto_step_retries = int(raw_retries)
    except (TypeError, ValueError):
        auto_step_retries = int(SERVER_OUTPUT_SPEC_DEFAULTS["auto_step_retries"])
    if auto_step_retries < 0:
        auto_step_retries = 0
    resolved["auto_step_retries"] = auto_step_retries

    raw_backoff = resolved.get("auto_step_backoff_s")
    try:
        auto_step_backoff_s = float(raw_backoff)
    except (TypeError, ValueError):
        auto_step_backoff_s = float(SERVER_OUTPUT_SPEC_DEFAULTS["auto_step_backoff_s"])
    if auto_step_backoff_s < 0:
        auto_step_backoff_s = 0.0
    resolved["auto_step_backoff_s"] = auto_step_backoff_s

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


async def resolve_runtime_execution_preferences(
    *,
    session: AsyncSession,
    brief_id: uuid.UUID,
) -> dict[str, Any]:
    defaults = await get_output_spec_defaults(session=session)
    merged = defaults

    def _as_int(key: str, *, fallback: int) -> int:
        raw = merged.get(key)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = fallback
        return max(0, value)

    def _as_float(key: str, *, fallback: float) -> float:
        raw = merged.get(key)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = fallback
        return max(0.0, value)

    return {
        "max_fix_attempts": _as_int("max_fix_attempts", fallback=int(defaults.get("max_fix_attempts") or 0)),
        "auto_step_retries": _as_int("auto_step_retries", fallback=int(defaults.get("auto_step_retries") or 0)),
        "auto_step_backoff_s": _as_float(
            "auto_step_backoff_s", fallback=float(defaults.get("auto_step_backoff_s") or 0.0)
        ),
    }


async def get_novel_to_script_prompt_defaults(*, session: AsyncSession) -> dict[str, Any]:
    setting = await session.get(AppSetting, NOVEL_TO_SCRIPT_PROMPT_DEFAULTS_KEY)
    stored = dict(setting.value or {}) if setting else {}
    conversion_notes = _normalize_optional_str(stored.get("conversion_notes"))
    return {"conversion_notes": conversion_notes}


async def patch_novel_to_script_prompt_defaults(
    *,
    session: AsyncSession,
    patch: dict[str, Any],
) -> dict[str, Any]:
    setting = await session.get(AppSetting, NOVEL_TO_SCRIPT_PROMPT_DEFAULTS_KEY)
    stored: dict[str, Any] = dict(setting.value or {}) if setting else {}

    raw = patch.get("conversion_notes", None)
    cleaned = _normalize_optional_str(raw)
    if cleaned is None:
        stored.pop("conversion_notes", None)
    else:
        stored["conversion_notes"] = cleaned

    if setting is None:
        setting = AppSetting(key=NOVEL_TO_SCRIPT_PROMPT_DEFAULTS_KEY, value=stored)
        session.add(setting)
    else:
        setting.value = stored

    await session.commit()
    return await get_novel_to_script_prompt_defaults(session=session)


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
