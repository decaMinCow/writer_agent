from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    @field_validator("hard_errors", mode="before")
    @classmethod
    def _coerce_hard_errors(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            cleaned = value.strip()
            return [cleaned] if cleaned else []
        if isinstance(value, list):
            items: list[str] = []
            for item in value:
                if item is None:
                    continue
                text = str(item).strip()
                if text:
                    items.append(text)
            return items
        return []

    @field_validator("soft_scores", mode="before")
    @classmethod
    def _coerce_soft_scores(cls, value: Any) -> dict[str, int]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            return {}
        cleaned: dict[str, int] = {}
        for key, raw in value.items():
            if key is None:
                continue
            try:
                score = int(raw)
            except (TypeError, ValueError):
                continue
            cleaned[str(key)] = score
        return cleaned

    @field_validator("rewrite_paragraph_indices", mode="before")
    @classmethod
    def _coerce_rewrite_paragraph_indices(cls, value: Any) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list):
            indices: list[int] = []
            for item in value:
                try:
                    idx = int(item)
                except (TypeError, ValueError):
                    continue
                if idx >= 1:
                    indices.append(idx)
            return indices
        try:
            idx = int(value)
        except (TypeError, ValueError):
            return []
        return [idx] if idx >= 1 else []

    @field_validator("rewrite_instructions", "fact_digest", "tone_digest", mode="before")
    @classmethod
    def _coerce_optional_str(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    @field_validator("state_patch", mode="before")
    @classmethod
    def _coerce_state_patch(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        return {}


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


class EpisodeBreakdown(BaseModel):
    episode_index: int = Field(ge=1)
    chapter_title: str = Field(default="")
    key_events: list[str] = Field(default_factory=list, min_length=1)
    conflicts: list[str] = Field(default_factory=list)
    emotional_beats: list[str] = Field(default_factory=list)
    relationship_changes: list[str] = Field(default_factory=list)
    hook_idea: str = Field(default="")


class NtsChapterPlanEpisode(BaseModel):
    sub_index: int = Field(ge=1)
    title: str = Field(default="")
    key_events: list[str] = Field(default_factory=list, min_length=1)
    conflicts: list[str] = Field(default_factory=list)
    emotional_beats: list[str] = Field(default_factory=list)
    relationship_changes: list[str] = Field(default_factory=list)
    hook_idea: str = Field(default="")


class NtsChapterPlan(BaseModel):
    chapter_index: int = Field(ge=1)
    chapter_title: str = Field(default="")
    core_plot: list[str] = Field(default_factory=list, min_length=1)
    episodes: list[NtsChapterPlanEpisode] = Field(min_length=1)

    @field_validator("episodes")
    @classmethod
    def _validate_episodes(cls, value: list[NtsChapterPlanEpisode]) -> list[NtsChapterPlanEpisode]:
        if not value:
            return value
        indices = [ep.sub_index for ep in value]
        if len(indices) != len(set(indices)):
            raise ValueError("duplicate_sub_index")
        if indices != sorted(indices):
            raise ValueError("sub_index_not_monotonic")
        if indices[0] != 1:
            raise ValueError("sub_index_must_start_at_1")
        return value


class CommittedArtifact(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_id: uuid.UUID
    artifact_version_id: uuid.UUID
