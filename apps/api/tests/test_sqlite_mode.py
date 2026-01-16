from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.core.config import Settings
from app.main import create_app


@pytest.mark.asyncio
async def test_sqlite_auto_migrate_creates_schema(tmp_path: Path):
    db_path = tmp_path / "writer_agent.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"

    settings = Settings(
        database_url=database_url,
        auto_migrate=True,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    app = create_app(settings=settings)
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        resp = await http_client.post("/api/briefs", json={"title": "sqlite test"})
        assert resp.status_code == 200
    await app.router.shutdown()

