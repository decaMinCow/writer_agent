from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.db.models import WorkflowKind
from app.llm.client import LLMClient
from app.schemas.brief_messages import BriefBuilderResult
from app.services.prompting import extract_json_object, load_prompt, render_prompt


async def build_brief_result(
    *,
    llm: LLMClient,
    current_brief_json: dict[str, Any],
    mode: WorkflowKind,
    user_message: str,
    max_attempts: int = 2,
) -> BriefBuilderResult:
    system_prompt = load_prompt("brief_builder_system.md")
    user_prompt = render_prompt(
        load_prompt("brief_builder_user.md"),
        {
            "CURRENT_BRIEF_JSON": json.dumps(current_brief_json, ensure_ascii=False, indent=2),
            "MODE": mode.value,
            "USER_MESSAGE": user_message,
        },
    )

    raw_output = await llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
    try:
        payload = extract_json_object(raw_output)
        return BriefBuilderResult.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        if max_attempts <= 1:
            raise RuntimeError("brief_builder_invalid_output") from exc

        repair_system = load_prompt("json_repair_system.md")
        repair_user = render_prompt(
            load_prompt("json_repair_user.md"),
            {"INVALID_OUTPUT": raw_output or str(exc)},
        )
        repaired = await llm.complete(system_prompt=repair_system, user_prompt=repair_user)
        try:
            payload = extract_json_object(repaired)
            return BriefBuilderResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as repair_exc:
            raise RuntimeError("brief_builder_invalid_output") from repair_exc
