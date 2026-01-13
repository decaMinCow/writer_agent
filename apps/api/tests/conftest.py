from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import asyncpg
import httpx
import pytest

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.main import create_app

API_ROOT = Path(__file__).resolve().parents[1]


def _replace_db(url: str, db_name: str) -> str:
    parsed = urlparse(url)
    return urlunparse(parsed._replace(path=f"/{db_name}"))


def _sqlalchemy_url_default() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/writer_agent",
    )


def _sqlalchemy_to_asyncpg_url(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+asyncpg://", "postgresql://")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    base = _sqlalchemy_url_default()
    db_name = os.getenv("TEST_DB_NAME", "writer_agent_test")
    return os.getenv("TEST_DATABASE_URL", _replace_db(base, db_name))


@pytest.fixture(scope="session")
async def _ensure_test_database(test_database_url: str) -> None:
    admin_url = _replace_db(_sqlalchemy_to_asyncpg_url(test_database_url), "postgres")
    target_db = urlparse(test_database_url).path.lstrip("/")

    conn = await asyncpg.connect(admin_url)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target_db)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{target_db}"')
    finally:
        await conn.close()

    env = dict(os.environ)
    env["DATABASE_URL"] = test_database_url
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(API_ROOT / "alembic.ini"), "upgrade", "head"],
        cwd=str(API_ROOT),
        check=True,
        env=env,
    )


@pytest.fixture()
async def app(_ensure_test_database: None, test_database_url: str):
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    return create_app(settings=settings)


@pytest.fixture()
async def client(app):
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await app.router.shutdown()


class StubLLM(LLMClient):
    def __init__(self) -> None:
        self.outputs: list[str] = []
        self.calls: list[dict[str, str]] = []

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if not self.outputs:
            raise RuntimeError("stub_llm_no_output")
        return self.outputs.pop(0)


@pytest.fixture()
def llm_stub() -> StubLLM:
    return StubLLM()


class StubEmbeddings(EmbeddingsClient):
    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        # Must match pgvector column dimension (1536).
        return [[1.0] + ([0.0] * 1535) for _ in texts]


@pytest.fixture()
def embeddings_stub() -> StubEmbeddings:
    return StubEmbeddings()


@pytest.fixture()
async def app_with_llm(_ensure_test_database: None, test_database_url: str, llm_stub: StubLLM):
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    return create_app(settings=settings, llm_client=llm_stub)


@pytest.fixture()
async def client_with_llm(app_with_llm):
    await app_with_llm.router.startup()
    transport = httpx.ASGITransport(app=app_with_llm)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await app_with_llm.router.shutdown()


@pytest.fixture()
async def app_with_llm_and_embeddings(
    _ensure_test_database: None, test_database_url: str, llm_stub: StubLLM, embeddings_stub: StubEmbeddings
):
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    return create_app(settings=settings, llm_client=llm_stub, embeddings_client=embeddings_stub)


@pytest.fixture()
async def client_with_llm_and_embeddings(app_with_llm_and_embeddings):
    await app_with_llm_and_embeddings.router.startup()
    transport = httpx.ASGITransport(app=app_with_llm_and_embeddings)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await app_with_llm_and_embeddings.router.shutdown()


@pytest.fixture(autouse=True)
async def _clean_database(_ensure_test_database: None, test_database_url: str) -> None:
    url = _sqlalchemy_to_asyncpg_url(test_database_url)
    conn = await asyncpg.connect(url)
    try:
        await conn.execute(
            """
            TRUNCATE TABLE
              app_settings,
              brief_messages,
              lint_issues,
              artifact_impacts,
              propagation_events,
              open_thread_refs,
              open_threads,
              snapshot_glossary_entries,
              kg_events,
              kg_relations,
              kg_entities,
              memory_chunks,
              artifact_versions,
              workflow_step_runs,
              workflow_runs,
              artifacts,
              brief_snapshots,
              briefs
            RESTART IDENTITY CASCADE
            """
        )
    finally:
        await conn.close()
