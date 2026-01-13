from __future__ import annotations

import pytest

from app.services.prompting import extract_json_object


def test_extract_json_object_allows_unescaped_newlines_in_strings() -> None:
    raw = '{\n  "title": "t",\n  "text": "a\nb"\n}\n'
    parsed = extract_json_object(raw)
    assert parsed["title"] == "t"
    assert parsed["text"] == "a\nb"


def test_extract_json_object_repairs_truncated_string_before_closing_brace() -> None:
    raw = '{\n  "title": "t",\n  "text": "a\nb\n}\n'
    parsed = extract_json_object(raw)
    assert parsed["title"] == "t"
    assert "a" in parsed["text"]


def test_extract_json_object_repairs_missing_closing_brace() -> None:
    raw = '{"title":"t","text":"a\nb'
    parsed = extract_json_object(raw)
    assert parsed["title"] == "t"
    assert parsed["text"].startswith("a")


def test_extract_json_object_raises_when_no_object_present() -> None:
    with pytest.raises(Exception):
        extract_json_object("not json at all")

