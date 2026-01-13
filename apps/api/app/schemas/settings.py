from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.briefs import ScriptFormat


class OutputSpecDefaultsRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: str
    script_format: ScriptFormat
    script_format_notes: str | None = None
    max_fix_attempts: int


class OutputSpecDefaultsPatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: str | None = None
    script_format: ScriptFormat | None = None
    script_format_notes: str | None = None
    max_fix_attempts: int | None = None


class LlmProviderSettingsRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    base_url: str | None = None
    model: str
    embeddings_model: str
    timeout_s: float
    max_retries: int
    api_key_configured: bool


class LlmProviderSettingsPatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    base_url: str | None = None
    model: str | None = None
    embeddings_model: str | None = None
    timeout_s: float | None = None
    max_retries: int | None = None
    api_key: str | None = None
