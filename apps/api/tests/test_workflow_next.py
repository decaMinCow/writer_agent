from __future__ import annotations

import json


async def test_novel_workflow_next_happy_path(client_with_llm_and_embeddings, llm_stub):
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
    llm_stub.outputs.append(
        json.dumps(
            {
                "chapters": [
                    {
                        "index": 1,
                        "title": "第一章：开端",
                        "beats": ["引子", "异常出现", "冲突升级", "信息揭示", "钩子结尾"],
                    }
                ]
            },
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(
        json.dumps({"title": "第一章：开端", "text": "第一段。\n\n第二段。"}, ensure_ascii=False)
    )
    llm_stub.outputs.append(
        json.dumps(
            {
                "hard_pass": True,
                "hard_errors": [],
                "soft_scores": {"tension": 70, "consistency": 80},
                "rewrite_paragraph_indices": [],
                "rewrite_instructions": "",
                "fact_digest": "主角发现异常。",
                "tone_digest": "紧张、快速推进。",
                "state_patch": {"chapter_index": 1},
            },
            ensure_ascii=False,
        )
    )

    step1 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step1.status_code == 200
    assert step1.json()["step"]["status"] == "succeeded"

    step2 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step2.status_code == 200
    assert step2.json()["step"]["status"] == "succeeded"

    step3 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step3.status_code == 200
    assert step3.json()["step"]["status"] == "succeeded"

    step4 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step4.status_code == 200
    assert step4.json()["step"]["status"] == "succeeded"

    step5 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step5.status_code == 200
    assert step5.json()["run"]["status"] == "succeeded"
    assert "artifact_version_id" in step5.json()["step"]["outputs"]


async def test_script_workflow_next_happy_path(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs",
        json={
            "title": "测试剧本",
            "content": {"output_spec": {"script_format": "screenplay_int_ext"}},
        },
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "script", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "scenes": [
                    {
                        "index": 1,
                        "slug": "s01",
                        "title": "夜里来电",
                        "location": "公寓客厅",
                        "time": "夜",
                        "characters": ["主角"],
                        "purpose": "引入悬念。",
                    }
                ]
            },
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(json.dumps({"text": "INT. 公寓客厅 - 夜\n\n主角接起电话。"}, ensure_ascii=False))
    llm_stub.outputs.append(
        json.dumps(
            {
                "hard_pass": True,
                "hard_errors": [],
                "soft_scores": {"shootable": 80},
                "rewrite_paragraph_indices": [],
                "rewrite_instructions": "",
                "fact_digest": "主角夜里接到电话。",
                "tone_digest": "悬疑、克制。",
                "state_patch": {"scene_index": 1},
            },
            ensure_ascii=False,
        )
    )

    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    done = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert done.json()["run"]["status"] == "succeeded"


async def test_novel_workflow_includes_memory_evidence(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs",
        json={
            "title": "测试作品",
            "content": {"output_spec": {"chapter_count": 2}, "logline": "一个人发现了一个秘密。"},
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

    llm_stub.outputs.append(
        json.dumps(
            {
                "chapters": [
                    {
                        "index": 1,
                        "title": "第一章：开端",
                        "summary": "主角发现异常并被卷入。",
                        "hook": "一个陌生号码发来一句话。",
                    },
                    {
                        "index": 2,
                        "title": "第二章：证据",
                        "summary": "线索浮现，代价上升。",
                        "hook": "电话里传来低笑。",
                    },
                ]
            },
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(
        json.dumps(
            {
                "chapters": [
                    {"index": 1, "title": "第一章：开端", "beats": ["引子", "异常出现", "冲突升级"]},
                    {"index": 2, "title": "第二章：证据", "beats": ["追索线索", "遭遇阻力", "代价出现"]},
                ]
            },
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(
        json.dumps(
            {"title": "第一章：开端", "text": "第一章证据片段。"},
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(
        json.dumps(
            {
                "hard_pass": True,
                "hard_errors": [],
                "soft_scores": {"tension": 70, "consistency": 80},
                "rewrite_paragraph_indices": [],
                "rewrite_instructions": "",
                "fact_digest": "主角发现异常。",
                "tone_digest": "紧张、快速推进。",
                "state_patch": {"chapter_index": 1},
            },
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(
        json.dumps({"title": "第二章：证据", "text": "第二章草稿。"}, ensure_ascii=False)
    )

    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")  # outline
    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")  # beats
    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")  # draft 1
    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")  # critic 1
    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")  # commit 1
    await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")  # draft 2

    assert llm_stub.calls
    last_prompt = llm_stub.calls[-1]["user_prompt"]
    assert "Evidence（可引用的已生成内容片段）：" in last_prompt
    assert "第一章证据片段" in last_prompt


async def test_commit_is_blocked_by_hard_check_failure(client_with_llm_and_embeddings):
    brief = await client_with_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={
            "kind": "novel",
            "brief_snapshot_id": snap_id,
            "status": "queued",
            "state": {
                "cursor": {"phase": "novel_chapter_commit", "chapter_index": 1},
                "beats": {"chapters": [{"index": 1, "title": "第一章", "beats": ["起"]}]},
                "draft": {"kind": "chapter", "index": 1, "title": "第一章", "text": "草稿。"},
                "critic": {"hard_pass": False, "hard_errors": ["dead_character_appears"]},
            },
        },
    )
    run_id = run.json()["id"]

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run"]["status"] == "failed"
    assert body["run"]["error"]["detail"] == "hard_check_failed"
    assert body["step"]["status"] == "failed"
    assert body["step"]["outputs"]["hard_pass"] is False


async def test_novel_to_script_fails_when_no_novel_sources(client_with_llm_and_embeddings):
    brief = await client_with_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel_to_script", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run"]["status"] == "failed"
    assert body["run"]["error"]["detail"] == "novel_source_missing"
    assert body["step"]["status"] == "failed"


async def test_novel_to_script_retry_resets_failed_cursor_phase(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel_to_script", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    first = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert first.status_code == 200
    assert first.json()["run"]["status"] == "failed"
    assert first.json()["run"]["error"]["detail"] == "novel_source_missing"

    artifact = await client_with_llm_and_embeddings.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]
    await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": "第一章内容",
            "metadata": {"fact_digest": "主角夜里接到电话。"},
            "brief_snapshot_id": snap_id,
        },
    )

    llm_stub.outputs.append(
        json.dumps(
            {
                "scenes": [
                    {
                        "index": 1,
                        "slug": "s01",
                        "title": "夜里来电",
                        "location": "公寓客厅",
                        "time": "夜",
                        "characters": ["主角"],
                        "purpose": "引入悬念。",
                    }
                ]
            },
            ensure_ascii=False,
        )
    )

    retried = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert retried.status_code == 200
    body = retried.json()
    assert body["step"]["step_name"] == "nts_scene_list"
    assert body["step"]["status"] == "succeeded"
    assert body["run"]["status"] == "running"
    assert "scene_list" in body["step"]["outputs"]


async def test_novel_to_script_can_use_different_source_snapshot(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap_source = await client_with_llm_and_embeddings.post(
        f"/api/briefs/{brief_id}/snapshots", json={"label": "source"}
    )
    snap_run = await client_with_llm_and_embeddings.post(
        f"/api/briefs/{brief_id}/snapshots", json={"label": "run"}
    )
    source_id = snap_source.json()["id"]
    run_id = snap_run.json()["id"]

    artifact = await client_with_llm_and_embeddings.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]
    await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": "第一章内容",
            "metadata": {"fact_digest": "主角夜里接到电话。"},
            "brief_snapshot_id": source_id,
        },
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={
            "kind": "novel_to_script",
            "brief_snapshot_id": run_id,
            "source_brief_snapshot_id": source_id,
            "status": "queued",
            "state": {},
        },
    )
    workflow_run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "scenes": [
                    {
                        "index": 1,
                        "slug": "s01",
                        "title": "夜里来电",
                        "location": "公寓客厅",
                        "time": "夜",
                        "characters": ["主角"],
                        "purpose": "引入悬念。",
                    }
                ]
            },
            ensure_ascii=False,
        )
    )

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{workflow_run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["step"]["status"] == "succeeded"
    assert body["run"]["status"] == "running"
    assert body["run"]["state"]["novel_source"]["source_snapshot_id"] == source_id


async def test_novel_to_script_uses_latest_chapter_versions_for_scene_list(
    client_with_llm_and_embeddings, llm_stub
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

    await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": "旧版本内容",
            "metadata": {"fact_digest": "旧摘要"},
            "brief_snapshot_id": snap_id,
        },
    )
    await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": "新版本内容",
            "metadata": {"fact_digest": "新摘要"},
            "brief_snapshot_id": snap_id,
        },
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel_to_script", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "scenes": [
                    {
                        "index": 1,
                        "slug": "s01",
                        "title": "场景一",
                        "location": "公寓客厅",
                        "time": "夜",
                        "characters": ["主角"],
                        "purpose": "引入悬念。",
                    }
                ]
            },
            ensure_ascii=False,
        )
    )

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    assert llm_stub.calls
    prompt = llm_stub.calls[-1]["user_prompt"]
    assert "新摘要" in prompt
    assert "旧摘要" not in prompt


async def test_novel_to_script_happy_path_and_honors_script_format(
    client_with_llm_and_embeddings, llm_stub
):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs",
        json={"title": "测试作品", "content": {"output_spec": {"script_format": "stage_play"}}},
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    artifact = await client_with_llm_and_embeddings.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]
    await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": "第一章内容",
            "metadata": {"fact_digest": "主角夜里接到电话。"},
            "brief_snapshot_id": snap_id,
        },
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel_to_script", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "scenes": [
                    {
                        "index": 1,
                        "slug": "s01",
                        "title": "夜里来电",
                        "location": "公寓客厅",
                        "time": "夜",
                        "characters": ["主角"],
                        "purpose": "引入悬念。",
                    }
                ]
            },
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(json.dumps({"text": "【场景一】\\n主角接起电话。"}, ensure_ascii=False))
    llm_stub.outputs.append(
        json.dumps(
            {
                "hard_pass": True,
                "hard_errors": [],
                "soft_scores": {"fidelity": 80, "shootability": 80},
                "rewrite_paragraph_indices": [],
                "rewrite_instructions": "",
                "fact_digest": "主角夜里接到电话。",
                "tone_digest": "悬疑、克制。",
                "state_patch": {"scene_index": 1},
            },
            ensure_ascii=False,
        )
    )

    step1 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step1.status_code == 200
    assert step1.json()["step"]["status"] == "succeeded"

    step2 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step2.status_code == 200
    assert step2.json()["step"]["status"] == "succeeded"
    assert llm_stub.calls
    draft_prompt = llm_stub.calls[-1]["user_prompt"]
    assert '"script_format": "stage_play"' in draft_prompt

    step3 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step3.status_code == 200
    assert step3.json()["step"]["status"] == "succeeded"

    step4 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step4.status_code == 200
    assert step4.json()["run"]["status"] == "succeeded"
    assert "artifact_version_id" in step4.json()["step"]["outputs"]


async def test_novel_to_script_conversion_output_spec_overrides_snapshot(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs",
        json={"title": "测试作品", "content": {"output_spec": {"script_format": "stage_play"}}},
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    artifact = await client_with_llm_and_embeddings.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]
    await client_with_llm_and_embeddings.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": "第一章内容",
            "metadata": {"fact_digest": "主角夜里接到电话。"},
            "brief_snapshot_id": snap_id,
        },
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={
            "kind": "novel_to_script",
            "brief_snapshot_id": snap_id,
            "conversion_output_spec": {
                "script_format": "custom",
                "script_format_notes": "PUA_TEST_NOTES",
            },
            "status": "queued",
            "state": {},
        },
    )
    run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "scenes": [
                    {
                        "index": 1,
                        "slug": "s01",
                        "title": "夜里来电",
                        "location": "公寓客厅",
                        "time": "夜",
                        "characters": ["主角"],
                        "purpose": "引入悬念。",
                    }
                ]
            },
            ensure_ascii=False,
        )
    )
    llm_stub.outputs.append(json.dumps({"text": "【场景一】\\n主角接起电话。"}, ensure_ascii=False))

    step1 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step1.status_code == 200
    assert step1.json()["step"]["status"] == "succeeded"

    step2 = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert step2.status_code == 200
    assert step2.json()["step"]["status"] == "succeeded"
    assert llm_stub.calls
    draft_prompt = llm_stub.calls[-1]["user_prompt"]
    assert '"script_format": "custom"' in draft_prompt
    assert "PUA_TEST_NOTES" in draft_prompt


async def test_create_novel_to_script_rejects_cross_brief_source_snapshot(client):
    brief_a = await client.post("/api/briefs", json={"title": "A", "content": {}})
    brief_b = await client.post("/api/briefs", json={"title": "B", "content": {}})
    snap_a = await client.post(f"/api/briefs/{brief_a.json()['id']}/snapshots", json={"label": "a1"})
    snap_b = await client.post(f"/api/briefs/{brief_b.json()['id']}/snapshots", json={"label": "b1"})

    resp = await client.post(
        "/api/workflow-runs",
        json={
            "kind": "novel_to_script",
            "brief_snapshot_id": snap_a.json()["id"],
            "source_brief_snapshot_id": snap_b.json()["id"],
            "status": "queued",
            "state": {},
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "source_snapshot_not_in_same_brief"


async def test_next_allows_retry_when_run_is_failed(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "failed", "state": {}},
    )
    run_id = run.json()["id"]

    patched = await client_with_llm_and_embeddings.patch(
        f"/api/workflow-runs/{run_id}", json={"error": {"detail": "pretend_failure"}}
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "failed"
    assert patched.json()["error"]["detail"] == "pretend_failure"

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

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["step"]["status"] == "succeeded"
    assert body["run"]["status"] == "running"
    assert body["run"]["error"] is None


async def test_next_returns_error_chain_when_step_fails(client_with_llm_and_embeddings):
    brief = await client_with_llm_and_embeddings.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()

    assert body["run"]["status"] == "failed"
    assert body["run"]["error"]["detail"] == "step_failed"
    assert "error_chain" in body["run"]["error"]
    assert "RuntimeError" in body["run"]["error"]["error_chain"]
    assert "stub_llm_no_output" in body["run"]["error"]["error_chain"]
    assert body["run"]["error"]["step_name"] == "novel_outline"
    assert body["run"]["error"]["step_index"] == 1
    assert "provider" in body["run"]["error"]

    assert body["step"]["status"] == "failed"
    assert "RuntimeError" in (body["step"]["error"] or "")
