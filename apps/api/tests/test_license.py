from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.core.config import Settings
from app.main import create_app
from app.services.license_store import get_machine_code


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _issue_license(*, private_key: Ed25519PrivateKey, machine_code: str) -> str:
    payload = {
        "license_id": str(uuid.uuid4()),
        "machine_code": machine_code,
        "issued_at": datetime.now(tz=timezone.utc).isoformat(),
        "expires_at": None,
        "features": {},
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    signature = private_key.sign(payload_bytes)
    return f"{_base64url_encode(payload_bytes)}.{_base64url_encode(signature)}"


@pytest.fixture()
async def client_with_license_required(_ensure_test_database: None, test_database_url: str):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    public_key_b64 = _base64url_encode(public_key)

    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
        license_public_key=public_key_b64,
        license_required=True,
        license_machine_salt="test-salt",
    )
    app = create_app(settings=settings)
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client, private_key, settings
    await app.router.shutdown()


async def test_license_blocks_api_calls_when_missing(client_with_license_required):
    client, _private_key, _settings = client_with_license_required
    resp = await client.post("/api/briefs", json={"title": "测试作品"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "license_required"


async def test_license_activation_allows_api_calls(client_with_license_required):
    client, private_key, settings = client_with_license_required
    machine_code = get_machine_code(settings=settings)
    license_code = _issue_license(private_key=private_key, machine_code=machine_code)

    activated = await client.post("/api/license/activate", json={"license_code": license_code})
    assert activated.status_code == 200
    assert activated.json()["authorized"] is True

    resp = await client.post("/api/briefs", json={"title": "测试作品"})
    assert resp.status_code == 200

