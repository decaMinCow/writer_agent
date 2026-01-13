from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import files
from typing import Any


@lru_cache
def load_prompt(filename: str) -> str:
    return (files("app.prompts") / filename).read_text(encoding="utf-8")


def render_prompt(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        if raw.endswith("```"):
            raw = raw[: -len("```")].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(raw[start : end + 1])

