from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from openai import APIConnectionError

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.main import create_app


class _StubEmbeddings(EmbeddingsClient):
    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        return [[1.0] + ([0.0] * 1535) for _ in texts]


class _FlakyOnceLLM(LLMClient):
    def __init__(self, *, outputs: list[str]) -> None:
        req = httpx.Request("POST", "http://test/v1/chat/completions")
        self.queue: list[object] = [APIConnectionError(message="Connection error.", request=req), *outputs]

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        if not self.queue:
            raise RuntimeError("stub_llm_no_output")
        item = self.queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return str(item)


class _AlwaysFailLLM(LLMClient):
    def __init__(self) -> None:
        self.req = httpx.Request("POST", "http://test/v1/chat/completions")

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        raise APIConnectionError(message="Connection error.", request=self.req)


@pytest.fixture()
async def client_with_flaky_llm_and_embeddings(_ensure_test_database: None, test_database_url: str):
    outputs = [
        json.dumps(
            {
                "chapters": [
                    {"index": 1, "title": "第一章", "summary": "开端。", "hook": "悬念。"},
                ]
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "chapters": [
                    {"index": 1, "title": "第一章", "beats": ["冲突出现", "角色选择", "留下钩子"]},
                ]
            },
            ensure_ascii=False,
        ),
        json.dumps({"title": "第一章", "text": "这是一段正文。"}, ensure_ascii=False),
        json.dumps(
            {
                "hard_pass": True,
                "hard_errors": [],
                "soft_scores": {"pacing": 7},
                "rewrite_paragraph_indices": [],
                "rewrite_instructions": "",
                "fact_digest": "角色做出了关键选择。",
                "tone_digest": "紧张但克制。",
                "state_patch": {},
            },
            ensure_ascii=False,
        ),
    ]
    llm = _FlakyOnceLLM(outputs=outputs)
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    app = create_app(settings=settings, llm_client=llm, embeddings_client=_StubEmbeddings())
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await app.router.shutdown()


@pytest.fixture()
async def client_with_failing_llm_and_embeddings(_ensure_test_database: None, test_database_url: str):
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    app = create_app(settings=settings, llm_client=_AlwaysFailLLM(), embeddings_client=_StubEmbeddings())
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await app.router.shutdown()


async def test_autorun_retries_retryable_failure_and_continues(client_with_flaky_llm_and_embeddings):
    await client_with_flaky_llm_and_embeddings.patch(
        "/api/settings/output-spec",
        json={"auto_step_retries": 2, "auto_step_backoff_s": 0.0},
    )

    brief = await client_with_flaky_llm_and_embeddings.post(
        "/api/briefs", json={"title": "测试作品", "content": {}}
    )
    brief_id = brief.json()["id"]
    snap = await client_with_flaky_llm_and_embeddings.post(
        f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"}
    )
    snap_id = snap.json()["id"]

    run = await client_with_flaky_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    started = await client_with_flaky_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/autorun/start")
    assert started.status_code == 200

    for _ in range(80):
        got = await client_with_flaky_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}")
        if got.json()["status"] == "succeeded":
            break
        await asyncio.sleep(0.02)

    got = await client_with_flaky_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}")
    assert got.json()["status"] == "succeeded"

    steps_resp = await client_with_flaky_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}/steps")
    steps = steps_resp.json()
    outline_steps = [s for s in steps if s["step_name"] == "novel_outline"]
    assert len(outline_steps) >= 2
    assert any(s["status"] == "failed" for s in outline_steps)
    assert any(s["status"] == "succeeded" for s in outline_steps)


async def test_autorun_stops_after_retry_limit_exhausted(client_with_failing_llm_and_embeddings):
    patched = await client_with_failing_llm_and_embeddings.patch(
        "/api/settings/output-spec",
        json={"auto_step_retries": 2, "auto_step_backoff_s": 0.0},
    )
    assert patched.status_code == 200
    assert patched.json()["auto_step_retries"] == 2
    assert patched.json()["auto_step_backoff_s"] == 0.0

    brief = await client_with_failing_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品"})
    brief_id = brief.json()["id"]
    snap = await client_with_failing_llm_and_embeddings.post(
        f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"}
    )
    snap_id = snap.json()["id"]
    assert snap.json()["content"]["output_spec"]["auto_step_retries"] == 2
    assert snap.json()["content"]["output_spec"]["auto_step_backoff_s"] == 0.0

    run = await client_with_failing_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    started = await client_with_failing_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/autorun/start")
    assert started.status_code == 200

    for _ in range(300):
        got = await client_with_failing_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}")
        if got.json()["status"] == "failed":
            break
        await asyncio.sleep(0.02)

    got = await client_with_failing_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}")
    body = got.json()
    assert body["status"] == "failed"
    assert body["error"]["autorun_retry_exhausted"] is True
    assert body["error"]["autorun_retry_limit"] == 2

    steps_resp = await client_with_failing_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}/steps")
    steps = steps_resp.json()
    # initial attempt + 2 retries
    assert len(steps) == 3
