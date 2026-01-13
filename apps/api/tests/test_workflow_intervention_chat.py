from __future__ import annotations

import json


async def test_workflow_intervention_applies_state_patch_and_records_step(client_with_llm, llm_stub):
    brief = await client_with_llm.post("/api/briefs", json={"title": "测试干预", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    step = await client_with_llm.post(
        f"/api/workflow-runs/{run_id}/steps",
        json={"step_name": "novel_outline", "step_index": 1, "status": "succeeded", "outputs": {"outline": {}}},
    )
    step_id = step.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "assistant_message": "已将流程调整到 beats 阶段。",
                "state_patch": {"cursor": {"phase": "novel_beats"}, "note": "test"},
            },
            ensure_ascii=False,
        )
    )

    resp = await client_with_llm.post(
        f"/api/workflow-runs/{run_id}/interventions",
        json={"instruction": "跳过大纲，直接进入分章。", "step_id": step_id},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["assistant_message"] == "已将流程调整到 beats 阶段。"
    assert body["state_patch"]["cursor"]["phase"] == "novel_beats"
    assert body["run"]["id"] == run_id
    assert body["run"]["state"]["cursor"]["phase"] == "novel_beats"
    assert body["run"]["state"]["note"] == "test"
    assert body["step"]["step_name"] == "intervention"
    assert body["step"]["outputs"]["target_step_id"] == step_id

    steps = await client_with_llm.get(f"/api/workflow-runs/{run_id}/steps")
    assert steps.status_code == 200
    assert any(s["step_name"] == "intervention" for s in steps.json())


async def test_workflow_intervention_requires_llm(client):
    brief = await client.post("/api/briefs", json={"title": "测试干预", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    resp = await client.post(
        f"/api/workflow-runs/{run_id}/interventions",
        json={"instruction": "测试", "step_id": None},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "openai_not_configured"


async def test_workflow_intervention_step_must_belong_to_run(client_with_llm, llm_stub):
    brief = await client_with_llm.post("/api/briefs", json={"title": "测试干预", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run1 = await client_with_llm.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run2 = await client_with_llm.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run1_id = run1.json()["id"]
    run2_id = run2.json()["id"]

    step = await client_with_llm.post(
        f"/api/workflow-runs/{run1_id}/steps",
        json={"step_name": "novel_outline", "step_index": 1, "status": "succeeded", "outputs": {}},
    )
    step_id = step.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {"assistant_message": "ok", "state_patch": {"cursor": {"phase": "novel_outline"}}},
            ensure_ascii=False,
        )
    )

    resp = await client_with_llm.post(
        f"/api/workflow-runs/{run2_id}/interventions",
        json={"instruction": "测试", "step_id": step_id},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "workflow_step_not_in_run"


async def test_workflow_intervention_allowed_when_run_failed(client_with_llm, llm_stub):
    brief = await client_with_llm.post("/api/briefs", json={"title": "测试干预", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "failed", "state": {}},
    )
    run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {"assistant_message": "已修正游标。", "state_patch": {"cursor": {"phase": "novel_outline"}}},
            ensure_ascii=False,
        )
    )

    resp = await client_with_llm.post(
        f"/api/workflow-runs/{run_id}/interventions",
        json={"instruction": "修正游标到大纲阶段。", "step_id": None},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["run"]["id"] == run_id
    assert body["step"]["step_name"] == "intervention"
