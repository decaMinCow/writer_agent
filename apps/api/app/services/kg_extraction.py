from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.llm.client import LLMClient
from app.services.prompting import extract_json_object, load_prompt, render_prompt


class KgExtractionEntity(BaseModel):
    name: str = Field(min_length=1)
    entity_type: str = Field(default="unknown", min_length=1)
    meta: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata", serialization_alias="metadata"
    )


class KgExtractionRelation(BaseModel):
    subject: str = Field(min_length=1)
    subject_type: str | None = None
    predicate: str = Field(min_length=1)
    object: str = Field(min_length=1)
    object_type: str | None = None
    meta: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata", serialization_alias="metadata"
    )


class KgExtractionEvent(BaseModel):
    event_key: str | None = None
    summary: str = Field(min_length=1)
    time_hint: str | None = None
    meta: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata", serialization_alias="metadata"
    )


class KgExtractionResult(BaseModel):
    entities: list[KgExtractionEntity] = Field(default_factory=list)
    relations: list[KgExtractionRelation] = Field(default_factory=list)
    events: list[KgExtractionEvent] = Field(default_factory=list)


async def extract_kg_for_artifact_version(
    *,
    llm: LLMClient,
    brief_json: dict[str, Any],
    artifact_meta: dict[str, Any],
    content_text: str,
) -> KgExtractionResult:
    raw = await llm.complete(
        system_prompt=load_prompt("kg_extract_system.md"),
        user_prompt=render_prompt(
            load_prompt("kg_extract_user.md"),
            {
                "BRIEF_JSON": json.dumps(brief_json, ensure_ascii=False, indent=2),
                "ARTIFACT_META_JSON": json.dumps(artifact_meta, ensure_ascii=False, indent=2),
                "CONTENT_TEXT": (content_text or "").strip(),
            },
        ),
    )
    payload = extract_json_object(raw)
    return KgExtractionResult.model_validate(payload)
