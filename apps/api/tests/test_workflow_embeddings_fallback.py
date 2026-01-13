from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.main import create_app


class _EmbeddingsNotAllowedError(Exception):
    status_code = 405


class _BadEmbeddings(EmbeddingsClient):
    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        raise _EmbeddingsNotAllowedError(
            "Client error '405 Method Not Allowed' for url 'http://test/v1/embeddings'"
        )


class _StubLLM(LLMClient):
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        if not self.outputs:
            raise RuntimeError("stub_llm_no_output")
        return self.outputs.pop(0)


@pytest.fixture()
async def client_with_llm_and_bad_embeddings(_ensure_test_database: None, test_database_url: str):
    llm = _StubLLM(outputs=[json.dumps({"title": "第一章", "text": "草稿。"}, ensure_ascii=False)])
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    app = create_app(settings=settings, llm_client=llm, embeddings_client=_BadEmbeddings())
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await app.router.shutdown()


async def test_chapter_draft_continues_when_embeddings_endpoint_not_supported(
    client_with_llm_and_bad_embeddings,
):
    brief = await client_with_llm_and_bad_embeddings.post(
        "/api/briefs",
        json={"title": "测试作品", "content": {}},
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_bad_embeddings.post(
        f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"}
    )
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_bad_embeddings.post(
        "/api/workflow-runs",
        json={
            "kind": "novel",
            "brief_snapshot_id": snap_id,
            "status": "queued",
            "state": {
                "cursor": {"phase": "novel_chapter_draft", "chapter_index": 1},
                "beats": {"chapters": [{"index": 1, "title": "第一章", "beats": ["起", "承", "转", "合", "钩子"]}]},
            },
        },
    )
    run_id = run.json()["id"]

    resp = await client_with_llm_and_bad_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()

    assert body["step"]["status"] == "succeeded"
    assert body["run"]["status"] == "running"
    assert body["run"]["state"]["cursor"]["phase"] == "novel_chapter_critic"
    assert body["run"]["state"]["rag"]["disabled"] is True
    assert body["run"]["state"]["rag"]["disabled_reason"] == "embeddings_endpoint_not_supported"
