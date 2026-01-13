from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NovelOutlineChapter(BaseModel):
    index: int = Field(ge=1)
    title: str
    summary: str
    hook: str


class NovelOutline(BaseModel):
    chapters: list[NovelOutlineChapter]


class NovelBeatsChapter(BaseModel):
    index: int = Field(ge=1)
    title: str
    beats: list[str] = Field(min_length=1)


class NovelBeats(BaseModel):
    chapters: list[NovelBeatsChapter]


class DraftResult(BaseModel):
    title: str | None = None
    text: str = Field(min_length=1)


class CriticResult(BaseModel):
    hard_pass: bool
    hard_errors: list[str] = Field(default_factory=list)
    soft_scores: dict[str, int] = Field(default_factory=dict)
    rewrite_paragraph_indices: list[int] = Field(default_factory=list)
    rewrite_instructions: str = Field(default="")
    fact_digest: str = Field(default="")
    tone_digest: str = Field(default="")
    state_patch: dict[str, Any] = Field(default_factory=dict)


class RewriteResult(BaseModel):
    replacements: dict[int, str] = Field(default_factory=dict)


class ScriptSceneListItem(BaseModel):
    index: int = Field(ge=1)
    slug: str
    title: str
    location: str
    time: str
    characters: list[str] = Field(default_factory=list)
    purpose: str = Field(default="")


class ScriptSceneList(BaseModel):
    scenes: list[ScriptSceneListItem]


class CommittedArtifact(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_id: uuid.UUID
    artifact_version_id: uuid.UUID

