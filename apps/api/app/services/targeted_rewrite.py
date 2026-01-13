from __future__ import annotations

import json
from typing import Any

from app.llm.client import LLMClient
from app.services.prompting import load_prompt, render_prompt


async def rewrite_selected_text(
    *,
    llm: LLMClient,
    brief_json: dict[str, Any],
    artifact_meta: dict[str, Any],
    instruction: str,
    selected_text: str,
    context_before: str,
    context_after: str,
) -> str:
    raw = await llm.complete(
        system_prompt=load_prompt("targeted_rewrite_system.md"),
        user_prompt=render_prompt(
            load_prompt("targeted_rewrite_user.md"),
            {
                "BRIEF_JSON": json.dumps(brief_json or {}, ensure_ascii=False, indent=2),
                "ARTIFACT_META_JSON": json.dumps(artifact_meta or {}, ensure_ascii=False, indent=2),
                "INSTRUCTION": (instruction or "").strip(),
                "SELECTED_TEXT": (selected_text or "").strip(),
                "CONTEXT_BEFORE": (context_before or "").strip(),
                "CONTEXT_AFTER": (context_after or "").strip(),
            },
        ),
    )
    return raw.strip()

