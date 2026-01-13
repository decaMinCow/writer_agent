from __future__ import annotations

import uuid

import asyncpg
import httpx
import pytest

from app.core.config import Settings
from app.llm.embeddings_client import EmbeddingsClient
from app.main import create_app


def _sqlalchemy_to_asyncpg_url(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+asyncpg://", "postgresql://")


async def _count_memory_chunks(*, test_database_url: str, artifact_version_id: str) -> int:
    conn = await asyncpg.connect(_sqlalchemy_to_asyncpg_url(test_database_url))
    try:
        return int(
            await conn.fetchval(
                "SELECT COUNT(*) FROM memory_chunks WHERE artifact_version_id = $1",
                uuid.UUID(artifact_version_id),
            )
            or 0
        )
    finally:
        await conn.close()


async def test_create_artifact_version_indexes_memory_when_embeddings_configured(
    client_with_llm_and_embeddings, test_database_url: str
):
    brief = await client_with_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    artifact = await client_with_llm_and_embeddings.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]

    created = await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={"source": "agent", "content_text": "第一章内容", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert created.status_code == 200
    version_id = created.json()["id"]

    assert await _count_memory_chunks(test_database_url=test_database_url, artifact_version_id=version_id) == 1


class _FailingEmbeddings(EmbeddingsClient):
    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embeddings_failed")


@pytest.fixture()
async def client_with_failing_embeddings(_ensure_test_database: None, test_database_url: str):
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    app = create_app(settings=settings, embeddings_client=_FailingEmbeddings())
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await app.router.shutdown()


async def test_create_artifact_version_is_best_effort_on_indexing_failure(
    client_with_failing_embeddings, test_database_url: str
):
    brief = await client_with_failing_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_failing_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    artifact = await client_with_failing_embeddings.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]

    created = await client_with_failing_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={"source": "agent", "content_text": "第一章内容", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert created.status_code == 200
    version_id = created.json()["id"]

    assert await _count_memory_chunks(test_database_url=test_database_url, artifact_version_id=version_id) == 0


async def test_create_artifact_version_succeeds_without_embeddings_and_skips_indexing(
    client, test_database_url: str
):
    brief = await client.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    artifact = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]

    created = await client.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={"source": "agent", "content_text": "第一章内容", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert created.status_code == 200
    version_id = created.json()["id"]

    assert await _count_memory_chunks(test_database_url=test_database_url, artifact_version_id=version_id) == 0

