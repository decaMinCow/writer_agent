from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import AppSetting

LICENSE_SETTINGS_KEY = "license_state"


def _normalize_optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    return cleaned or None


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _base64url_decode(text: str) -> bytes:
    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _read_machine_code_raw() -> str:
    if sys.platform == "darwin":
        try:
            output = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"], text=True
            )
            match = re.search(r"IOPlatformUUID\"\\s*=\\s*\"([^\"]+)\"", output)
            if match:
                return match.group(1)
        except Exception:
            pass

    if sys.platform.startswith("win"):
        try:
            import winreg  # type: ignore

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Cryptography"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                if value:
                    return str(value)
        except Exception:
            pass

    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as handle:
                    raw = handle.read().strip()
                    if raw:
                        return raw
        except Exception:
            continue

    return platform.node() or "unknown-machine"


def get_machine_code(*, settings: Settings) -> str:
    raw = _read_machine_code_raw()
    salted = f"{raw}|{settings.license_machine_salt}".encode("utf-8")
    digest = hashlib.sha256(salted).hexdigest()
    return digest


def _public_key_from_settings(settings: Settings) -> Ed25519PublicKey | None:
    raw = _normalize_optional_str(settings.license_public_key)
    if not raw:
        return None
    try:
        key_bytes = _base64url_decode(raw)
    except Exception:
        try:
            key_bytes = bytes.fromhex(raw)
        except Exception:
            return None
    try:
        return Ed25519PublicKey.from_public_bytes(key_bytes)
    except Exception:
        return None


def _decode_license_payload(license_code: str) -> tuple[dict[str, Any], bytes]:
    parts = [part for part in (license_code or "").strip().split(".") if part]
    if len(parts) != 2:
        raise ValueError("invalid_license_format")
    payload_bytes = _base64url_decode(parts[0])
    signature = _base64url_decode(parts[1])
    payload = json.loads(payload_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid_license_payload")
    return payload, signature


def _validate_payload(*, payload: dict[str, Any], machine_code: str) -> None:
    bound = _normalize_optional_str(payload.get("machine_code"))
    if not bound or bound != machine_code:
        raise ValueError("license_machine_mismatch")

    expires_at = _parse_iso_datetime(_normalize_optional_str(payload.get("expires_at")))
    if expires_at and expires_at < datetime.now(tz=timezone.utc):
        raise ValueError("license_expired")


def validate_license_code(
    *,
    license_code: str,
    machine_code: str,
    settings: Settings,
) -> dict[str, Any]:
    public_key = _public_key_from_settings(settings)
    if public_key is None:
        raise ValueError("license_public_key_missing")

    payload, signature = _decode_license_payload(license_code)
    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    try:
        public_key.verify(signature, payload_bytes)
    except Exception as exc:
        raise ValueError("license_signature_invalid") from exc

    _validate_payload(payload=payload, machine_code=machine_code)
    return payload


async def get_license_record(*, session: AsyncSession) -> dict[str, Any] | None:
    setting = await session.get(AppSetting, LICENSE_SETTINGS_KEY)
    if setting is None or not isinstance(setting.value, dict):
        return None
    return dict(setting.value)


async def store_license_record(*, session: AsyncSession, record: dict[str, Any]) -> None:
    setting = await session.get(AppSetting, LICENSE_SETTINGS_KEY)
    if setting is None:
        setting = AppSetting(key=LICENSE_SETTINGS_KEY, value=record)
        session.add(setting)
    else:
        setting.value = record
    await session.commit()


async def clear_license_record(*, session: AsyncSession) -> None:
    setting = await session.get(AppSetting, LICENSE_SETTINGS_KEY)
    if setting is None:
        return
    await session.delete(setting)
    await session.commit()


async def license_status(*, session: AsyncSession, settings: Settings) -> dict[str, Any]:
    enabled = bool(settings.license_required or settings.license_public_key)
    machine_code = get_machine_code(settings=settings)
    record = await get_license_record(session=session)
    license_code = _normalize_optional_str(record.get("license_code") if record else None)
    payload: dict[str, Any] | None = None
    error: str | None = None

    if license_code:
        try:
            payload = validate_license_code(
                license_code=license_code, machine_code=machine_code, settings=settings
            )
        except ValueError as exc:
            error = str(exc)

    authorized = bool(payload) if enabled else True
    return {
        "enabled": enabled,
        "authorized": authorized,
        "machine_code": machine_code,
        "license": payload,
        "error": error,
    }

