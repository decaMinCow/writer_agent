from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.llm.client import LLMClient
from app.services.prompting import extract_json_object, load_prompt, render_prompt


class PropagationDiffResult(BaseModel):
    fact_changes: str = Field(default="")
    patches: dict[str, Any] = Field(default_factory=dict)


async def extract_fact_changes(
    *,
    llm: LLMClient,
    brief_json: dict[str, Any],
    base_meta: dict[str, Any],
    edited_meta: dict[str, Any],
    base_text: str,
    edited_text: str,
) -> PropagationDiffResult:
    raw = await llm.complete(
        system_prompt=load_prompt("propagation_extract_system.md"),
        user_prompt=render_prompt(
            load_prompt("propagation_extract_user.md"),
            {
                "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                "BASE_META_JSON": json.dumps(base_meta, ensure_ascii=False, indent=2),
                "EDITED_META_JSON": json.dumps(edited_meta, ensure_ascii=False, indent=2),
                "BASE_TEXT": (base_text or "").strip(),
                "EDITED_TEXT": (edited_text or "").strip(),
            },
        ),
    )
    payload = extract_json_object(raw)
    return PropagationDiffResult.model_validate(payload)


async def repair_impacted_content(
    *,
    llm: LLMClient,
    brief_json: dict[str, Any],
    fact_changes: str,
    upstream_edited_text: str,
    impacted_meta: dict[str, Any],
    impacted_text: str,
) -> str:
    raw = await llm.complete(
        system_prompt=load_prompt("propagation_repair_system.md"),
        user_prompt=render_prompt(
            load_prompt("propagation_repair_user.md"),
            {
                "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                "FACT_CHANGES": (fact_changes or "").strip(),
                "UPSTREAM_EDITED_TEXT": (upstream_edited_text or "").strip(),
                "IMPACTED_META_JSON": json.dumps(impacted_meta, ensure_ascii=False, indent=2),
                "IMPACTED_TEXT": (impacted_text or "").strip(),
            },
        ),
    )
    return raw.strip()

