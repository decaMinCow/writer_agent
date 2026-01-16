from __future__ import annotations

import json


async def _create_novel_chapter(client, *, snapshot_id: str, ordinal: int, title: str, content_text: str) -> None:
    artifact = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": ordinal, "title": title},
    )
    artifact_id = artifact.json()["id"]
    await client.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": content_text,
            "metadata": {"fact_digest": f"{title} 摘要。", "chapter_title": title},
            "brief_snapshot_id": snapshot_id,
        },
    )


async def test_novel_to_script_defaults_to_episode_breakdown(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs", json={"title": "测试作品", "content": {"output_spec": {"script_format": "custom"}}}
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    await _create_novel_chapter(
        client_with_llm_and_embeddings,
        snapshot_id=snap_id,
        ordinal=1,
        title="第一章：开场",
        content_text="第一章内容：主角出场，遭遇危机。",
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel_to_script", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "episode_index": 1,
                "chapter_title": "第一章：开场",
                "key_events": ["主角出场并遭遇危机。"],
                "conflicts": ["主角与未知威胁对峙。"],
                "emotional_beats": ["紧张升级。"],
                "relationship_changes": [],
                "hook_idea": "危机骤然加深。",
            },
            ensure_ascii=False,
        )
    )

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["step"]["step_name"] == "nts_episode_breakdown"
    assert body["run"]["state"]["cursor"]["phase"] == "nts_episode_draft"
    assert body["run"]["state"]["cursor"]["chapter_index"] == 1
    assert "episode_breakdown" in body["run"]["state"]


async def test_novel_to_script_episode_format_guard_routes_to_fix(client_with_llm_and_embeddings):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs", json={"title": "测试作品", "content": {"output_spec": {"script_format": "custom"}}}
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    await _create_novel_chapter(
        client_with_llm_and_embeddings,
        snapshot_id=snap_id,
        ordinal=1,
        title="第一章：开场",
        content_text="第一章内容：主角出场，遭遇危机。",
    )

    # Draft contains duplicated episode headers and duplicated/non-monotonic scene numbers.
    draft_text = (
        "第1集\n\n"
        "1-1\n日\n内\n地点：杂货铺\n出场人物：主角\n\n主角：开始。\n\n"
        "第1集\n\n"
        "1-1\n夜\n外\n地点：街口\n出场人物：主角\n\n主角：重复了。\n"
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={
            "kind": "novel_to_script",
            "brief_snapshot_id": snap_id,
            "status": "queued",
            "state": {
                "conversion_output_spec": {"script_format": "custom"},
                "cursor": {"phase": "nts_episode_critic", "chapter_index": 1},
                "draft": {"kind": "episode", "index": 1, "text": draft_text},
                "fix_attempt": 0,
            },
        },
    )
    run_id = run.json()["id"]

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["step"]["step_name"] == "nts_episode_critic"
    assert body["step"]["status"] == "succeeded"
    assert body["run"]["state"]["cursor"]["phase"] == "nts_episode_fix"
    assert body["step"]["outputs"]["hard_pass"] is False
    assert "format_multiple_episode_headers" in body["step"]["outputs"]["hard_errors"]
    assert "format_scene_blocks_duplicate" in body["step"]["outputs"]["hard_errors"]


async def test_novel_to_script_episode_accepts_chinese_episode_header(client_with_llm_and_embeddings, llm_stub):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs", json={"title": "测试作品", "content": {"output_spec": {"script_format": "custom"}}}
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    await _create_novel_chapter(
        client_with_llm_and_embeddings,
        snapshot_id=snap_id,
        ordinal=1,
        title="第一章：开场",
        content_text="第一章内容：主角出场，遭遇危机。",
    )

    draft_text = (
        "第一集\n\n"
        "1-1\n日\n内\n地点：杂货铺\n出场人物：主角\n\n△昏黄灯光。\n主角：开始。\n"
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={
            "kind": "novel_to_script",
            "brief_snapshot_id": snap_id,
            "status": "queued",
            "state": {
                "conversion_output_spec": {"script_format": "custom"},
                "cursor": {"phase": "nts_episode_critic", "chapter_index": 1},
                "draft": {"kind": "episode", "index": 1, "text": draft_text},
                "fix_attempt": 0,
            },
        },
    )
    run_id = run.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "hard_pass": True,
                "hard_errors": [],
                "soft_scores": {"fidelity": 90},
                "rewrite_paragraph_indices": [],
                "rewrite_instructions": "",
                "fact_digest": "主角出场并遭遇危机。",
                "tone_digest": "紧张。",
                "state_patch": {},
            },
            ensure_ascii=False,
        )
    )

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["step"]["step_name"] == "nts_episode_critic"
    assert body["step"]["outputs"]["hard_pass"] is True
    assert body["run"]["state"]["cursor"]["phase"] == "nts_episode_commit"


async def test_novel_to_script_episode_happy_path_commits_one_script_per_chapter(
    client_with_llm_and_embeddings, llm_stub
):
    brief = await client_with_llm_and_embeddings.post(
        "/api/briefs", json={"title": "测试作品", "content": {"output_spec": {"script_format": "custom"}}}
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm_and_embeddings.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    await _create_novel_chapter(
        client_with_llm_and_embeddings,
        snapshot_id=snap_id,
        ordinal=1,
        title="第一章：开场",
        content_text="第一章内容：主角出场。",
    )
    await _create_novel_chapter(
        client_with_llm_and_embeddings,
        snapshot_id=snap_id,
        ordinal=2,
        title="第二章：升级",
        content_text="第二章内容：冲突升级。",
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={"kind": "novel_to_script", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    run_id = run.json()["id"]

    llm_stub.outputs.extend(
        [
            json.dumps(
                {
                    "episode_index": 1,
                    "chapter_title": "第一章：开场",
                    "key_events": ["主角出场。"],
                    "conflicts": ["埋下危机。"],
                    "emotional_beats": ["建立氛围。"],
                    "relationship_changes": [],
                    "hook_idea": "危机出现。",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "title": "开场",
                    "text": "第1集\n\n1-1\n日\n内\n地点：杂货铺\n出场人物：主角\n\n△杂货铺昏黄。\n主角：今天不对劲。\n\n1-2\n日\n外\n地点：门口\n出场人物：主角\n\n△风铃大作。\n主角：谁在外面？",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "hard_pass": True,
                    "hard_errors": [],
                    "soft_scores": {"fidelity": 90},
                    "rewrite_paragraph_indices": [],
                    "rewrite_instructions": "",
                    "fact_digest": "主角出场并察觉异常。",
                    "tone_digest": "诡异紧张。",
                    "state_patch": {},
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "episode_index": 2,
                    "chapter_title": "第二章：升级",
                    "key_events": ["冲突升级。"],
                    "conflicts": ["威胁逼近。"],
                    "emotional_beats": ["压力上升。"],
                    "relationship_changes": [],
                    "hook_idea": "更大的麻烦。",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "title": "升级",
                    "text": "第2集\n\n2-1\n夜\n内\n地点：杂货铺\n出场人物：主角\n\n△灯光闪烁。\n主角：它来了。\n\n2-2\n夜\n外\n地点：街口\n出场人物：主角\n\n△黑影逼近。\n主角：别过来！",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "hard_pass": True,
                    "hard_errors": [],
                    "soft_scores": {"fidelity": 92},
                    "rewrite_paragraph_indices": [],
                    "rewrite_instructions": "",
                    "fact_digest": "危机升级，威胁逼近。",
                    "tone_digest": "节奏加快。",
                    "state_patch": {},
                },
                ensure_ascii=False,
            ),
        ]
    )

    # 2 chapters: 8 steps (breakdown, draft, critic, commit) x2
    for _ in range(8):
        resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
        assert resp.status_code == 200

    run_read = await client_with_llm_and_embeddings.get(f"/api/workflow-runs/{run_id}")
    assert run_read.status_code == 200
    assert run_read.json()["status"] == "succeeded"

    artifacts = await client_with_llm_and_embeddings.get(f"/api/artifacts?brief_snapshot_id={snap_id}")
    script_artifacts = [a for a in artifacts.json() if a["kind"] == "script_scene"]
    ordinals = sorted([a["ordinal"] for a in script_artifacts])
    assert ordinals == [1, 2]

    for artifact in script_artifacts:
        versions = await client_with_llm_and_embeddings.get(
            f"/api/artifacts/{artifact['id']}/versions?brief_snapshot_id={snap_id}"
        )
        assert versions.status_code == 200
        assert len(versions.json()) == 1
        text = versions.json()[0]["content_text"]
        assert f"第{artifact['ordinal']}集" in text
