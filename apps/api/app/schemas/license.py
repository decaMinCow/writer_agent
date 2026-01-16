from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LicenseActivateRequest(BaseModel):
    license_code: str


class LicenseStatusResponse(BaseModel):
    enabled: bool
    authorized: bool
    machine_code: str
    license: dict[str, Any] | None = None
    error: str | None = None
