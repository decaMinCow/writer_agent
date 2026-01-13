from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import pytest

from app.core.config import Settings
from app.llm.client import LLMClient
from app.main import create_app


class _StreamingStubLLM(LLMClient):
    def __init__(self, *, chunks: list[str]) -> None:
        self.chunks = list(chunks)
        self.stream_calls: list[dict[str, str]] = []
        self.complete_calls: list[dict[str, str]] = []

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        self.complete_calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        raise RuntimeError("unexpected_complete_call")

    async def stream_complete(self, *, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        self.stream_calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        for chunk in self.chunks:
            yield chunk


@pytest.fixture()
async def client_with_streaming_llm(_ensure_test_database: None, test_database_url: str):
    payload_obj = {
        "assistant_message": "好的，我先补充一句话卖点，并给你追问几个关键点。",
        "brief_patch": {"content": {"logline": "一名实习编辑卷入连环失踪案。"}, "title": "失踪编辑"},
        "gap_report": {
            "mode": "novel",
            "confirmed": ["title", "logline"],
            "pending": [],
            "missing": ["characters.main", "world.rules"],
            "conflict": [],
            "questions": ["主角是谁？他/她最想要什么？", "故事发生在哪个城市/时代？"],
            "completeness": 30,
        },
    }
    full = json.dumps(payload_obj, ensure_ascii=False, separators=(",", ":"))
    needle = '"assistant_message":"'
    start = full.index(needle) + len(needle)
    chunks = [full[: start + 1], full[start + 1 : start + 2], full[start + 2 :]]

    llm = _StreamingStubLLM(chunks=chunks)
    settings = Settings(
        database_url=test_database_url,
        cors_allow_origins="http://localhost:5173,http://127.0.0.1:5173",
    )
    app = create_app(settings=settings, llm_client=llm)
    await app.router.startup()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client, llm
    await app.router.shutdown()


def _parse_sse(text: str) -> list[tuple[str, str]]:
    events: list[tuple[str, str]] = []
    for block in text.split("\n\n"):
        if not block.strip():
            continue
        name = ""
        data = ""
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line.replace("event: ", "", 1)
            if line.startswith("data: "):
                data = line.replace("data: ", "", 1)
        if name:
            events.append((name, data))
    return events


async def test_brief_message_stream_sends_deltas_and_final(client_with_streaming_llm):
    client, llm = client_with_streaming_llm

    brief = await client.post("/api/briefs", json={"title": "测试作品"})
    brief_id = brief.json()["id"]

    resp = await client.post(
        f"/api/briefs/{brief_id}/messages/stream",
        json={"content_text": "我想写一个都市悬疑", "mode": "novel"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    assert any(name == "assistant_delta" for name, _ in events)

    final_data = next((data for name, data in events if name == "final"), None)
    assert final_data is not None
    payload = json.loads(final_data)
    assert payload["brief"]["title"] == "失踪编辑"
    assert payload["brief"]["content"]["logline"] == "一名实习编辑卷入连环失踪案。"
    assert payload["gap_report"]["completeness"] == 30

    messages = payload["messages"]
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content_text"] == "我想写一个都市悬疑"
    assert messages[-1]["role"] == "assistant"

    assert len(llm.stream_calls) == 1
    assert len(llm.complete_calls) == 0

