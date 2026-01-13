from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.briefs import ScriptFormat


class OutputSpecDefaultsRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: str
    script_format: ScriptFormat
    script_format_notes: str | None = None


class OutputSpecDefaultsPatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: str | None = None
    script_format: ScriptFormat | None = None
    script_format_notes: str | None = None

