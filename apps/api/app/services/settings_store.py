from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AppSetting
from app.schemas.briefs import ScriptFormat
from app.services.json_utils import deep_merge

OUTPUT_SPEC_DEFAULTS_KEY = "output_spec_defaults"

SERVER_OUTPUT_SPEC_DEFAULTS: dict[str, Any] = {
    "language": "zh-CN",
    "script_format": ScriptFormat.screenplay_int_ext.value,
    "script_format_notes": None,
}


async def get_output_spec_defaults(*, session: AsyncSession) -> dict[str, Any]:
    setting = await session.get(AppSetting, OUTPUT_SPEC_DEFAULTS_KEY)
    stored = dict(setting.value or {}) if setting else {}
    resolved = deep_merge(SERVER_OUTPUT_SPEC_DEFAULTS, stored)

    if not resolved.get("language"):
        resolved["language"] = SERVER_OUTPUT_SPEC_DEFAULTS["language"]
    if not resolved.get("script_format"):
        resolved["script_format"] = SERVER_OUTPUT_SPEC_DEFAULTS["script_format"]

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

