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


def _loads_best_effort(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = json.loads(raw, strict=False)
    if not isinstance(parsed, dict):
        raise ValueError("expected_json_object")
    return parsed


def _repair_truncated_json_object(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return text

    in_string = False
    escape = False
    brace_balance = 0
    bracket_balance = 0

    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            brace_balance += 1
        elif ch == "}":
            brace_balance = max(0, brace_balance - 1)
        elif ch == "[":
            bracket_balance += 1
        elif ch == "]":
            bracket_balance = max(0, bracket_balance - 1)

    repaired = text

    # If we're still inside a string and the output ends with a bracket/brace, it's often because
    # the model forgot the closing quote. Insert it before the trailing bracket/brace so that the
    # bracket/brace can act as structural JSON again (instead of being part of the string).
    if in_string:
        stripped = repaired.rstrip()
        if stripped and stripped[-1] in {"}", "]"}:
            last = stripped[-1]
            repaired = stripped[:-1] + '"' + last
            if last == "}":
                brace_balance = max(0, brace_balance - 1)
            else:
                bracket_balance = max(0, bracket_balance - 1)
            in_string = False
            escape = False

    if escape:
        repaired += "\\"
        escape = False

    if in_string:
        repaired += '"'
        in_string = False

    repaired += "]" * bracket_balance
    repaired += "}" * brace_balance
    return repaired


def extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        if raw.endswith("```"):
            raw = raw[: -len("```")].strip()

    try:
        return _loads_best_effort(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1:
            raise

        candidates: list[str] = []
        if end != -1 and end > start:
            candidates.append(raw[start : end + 1])
        candidates.append(raw[start:])

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                return _loads_best_effort(candidate)
            except Exception as exc:  # noqa: BLE001 - best-effort parsing
                last_error = exc

            repaired = _repair_truncated_json_object(candidate)
            if repaired and repaired != candidate:
                try:
                    return _loads_best_effort(repaired)
                except Exception as exc:  # noqa: BLE001 - best-effort parsing
                    last_error = exc

        if last_error is not None:
            raise last_error
        raise
