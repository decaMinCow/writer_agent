from __future__ import annotations

import json
import uuid

import asyncpg


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


async def test_fork_workflow_run_copies_state_and_is_runnable(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs",
        json={
            "title": "测试作品",
            "content": {"output_spec": {"chapter_count": 1}, "logline": "一个人发现了一个秘密。"},
        },
    )
    brief_id = brief.json()["id"]

    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    forked = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/fork", json={})
    assert forked.status_code == 200
    fork_id = forked.json()["id"]
    assert forked.json()["kind"] == "novel"
    assert forked.json()["brief_snapshot_id"] == snap_id
    assert forked.json()["status"] == "queued"
    assert forked.json()["state"]["forked_from"]["run_id"] == run_id

    llm_stub.outputs.append(
        json.dumps(
            {
                "chapters": [
                    {
                        "index": 1,
                        "title": "第一章：开端",
                        "summary": "主角发现异常并被卷入。",
                        "hook": "一个陌生号码发来一句话。",
                    }
                ]
            },
            ensure_ascii=False,
        )
    )

    step1 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{fork_id}/next")
    assert step1.status_code == 200
    assert step1.json()["step"]["status"] == "succeeded"


async def test_targeted_rewrite_creates_new_version_and_indexes_memory(
    client_with_llm_and_embeddings, llm_stub, test_database_url: str
):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs",
        json={"title": "测试作品", "content": {"logline": "一个人发现了一个秘密。"}},
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    artifact = await client_with_llm_and_embeddings.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]

    base_text = "他回到旧城，雨一直下。"
    base_version = await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={"source": "agent", "content_text": base_text, "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert base_version.status_code == 200
    base_version_id = base_version.json()["id"]
    assert await _count_memory_chunks(test_database_url=test_database_url, artifact_version_id=base_version_id) == 1

    start = base_text.index("旧城")
    end = start + len("旧城")

    llm_stub.outputs.append("新城")

    rewritten = await client_with_llm_and_embeddings.post(
        f"/api/artifacts/versions/{base_version_id}/rewrite",
        json={"instruction": "把旧城改成新城", "selection_start": start, "selection_end": end},
    )
    assert rewritten.status_code == 200
    new_version_id = rewritten.json()["id"]
    assert "新城" in rewritten.json()["content_text"]
    assert rewritten.json()["metadata"]["rewritten_from_version_id"] == base_version_id

    assert await _count_memory_chunks(test_database_url=test_database_url, artifact_version_id=new_version_id) == 1

