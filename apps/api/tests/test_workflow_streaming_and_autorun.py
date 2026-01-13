from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.main import create_app


async def test_workflow_events_stream_sends_initial_run_event(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    resp = await client.get(f"/api/workflow-runs/{run_id}/events?once=1")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    text = resp.text
    assert "event: run" in text
    data_line = next((line for line in text.splitlines() if line.startswith("data: ")), "")
    payload = json.loads(data_line.replace("data: ", "", 1))
    assert payload["run"]["id"] == run_id


class _SlowStubLLM(LLMClient):
    def __init__(self, *, outputs: list[str], delay_s: float = 0.2) -> None:
        self.outputs = list(outputs)
        self.delay_s = delay_s

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        await asyncio.sleep(self.delay_s)
        if not self.outputs:
            raise RuntimeError("stub_llm_no_output")
        return self.outputs.pop(0)


class _StubEmbeddings(EmbeddingsClient):
    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        return [[1.0] + ([0.0] * 1535) for _ in texts]


@pytest.fixture()
async def client_with_slow_llm_and_embeddings(_ensure_test_database: None, test_database_url: str):
    llm = _SlowStubLLM(
        outputs=[
            json.dumps(
                {
                    "chapters": [
                        {
                            "index": 1,
                            "title": "第一章",
                            "summary": "开端。",
                            "hook": "悬念。",
                        }
                    ]
                },
                ensure_ascii=False,
            )
        ],
        delay_s=0.25,
    )
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


async def test_autorun_stop_prevents_additional_steps(client_with_slow_llm_and_embeddings):
    brief = await client_with_slow_llm_and_embeddings.post(
        "/api/briefs", json={"title": "测试作品", "content": {}}
    )
    brief_id = brief.json()["id"]
    snap = await client_with_slow_llm_and_embeddings.post(
        f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"}
    )
    snap_id = snap.json()["id"]

    run = await client_with_slow_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    started = await client_with_slow_llm_and_embeddings.post(
        f"/api/workflow-runs/{run_id}/autorun/start"
    )
    assert started.status_code == 200

    for _ in range(40):
        steps_resp = await client_with_slow_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}/steps")
        steps = steps_resp.json()
        if len(steps) >= 1:
            break
        await asyncio.sleep(0.02)

    steps_resp = await client_with_slow_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}/steps")
    steps = steps_resp.json()
    assert len(steps) == 1

    stopped = await client_with_slow_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/autorun/stop")
    assert stopped.status_code == 200

    await asyncio.sleep(0.4)
    steps_resp_after = await client_with_slow_llm_and_embeddings.get(
        f"/api/workflow-runs/{run_id}/steps"
    )
    steps_after = steps_resp_after.json()
    assert len(steps_after) == 1
