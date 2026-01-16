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


def _long_scene_text(*, episode_index: int, title: str) -> str:
    filler = ("啊" if episode_index % 2 else "哈") * 280
    return (
        f"第{episode_index}集\n\n"
        f"{episode_index}-1\n日\n内\n地点：杂货铺\n出场人物：主角\n\n"
        f"△{filler}\n\n"
        f"{episode_index}-2\n夜\n外\n地点：门口\n出场人物：主角\n\n"
        f"△{filler}"
    )


async def test_novel_to_script_auto_split_starts_with_chapter_plan_and_commits_multiple_episodes(
    client_with_llm_and_embeddings, llm_stub
):
    await client_with_llm_and_embeddings.patch(
        "/api/settings/output-spec",
        json={"script_format": "custom"},
    )
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
        json={
            "kind": "novel_to_script",
            "brief_snapshot_id": snap_id,
            "split_mode": "auto_by_length",
            "status": "queued",
            "state": {},
        },
    )
    run_id = run.json()["id"]

    llm_stub.outputs.extend(
        [
            json.dumps(
                {
                    "chapter_index": 1,
                    "chapter_title": "第一章：开场",
                    "core_plot": ["主角出场并遭遇危机。"],
                    "episodes": [
                        {
                            "sub_index": 1,
                            "title": "开场",
                            "key_events": ["主角出场。"],
                            "conflicts": ["危机出现。"],
                            "emotional_beats": ["紧张升级。"],
                            "relationship_changes": [],
                            "hook_idea": "危机加深。",
                        },
                        {
                            "sub_index": 2,
                            "title": "危机",
                            "key_events": ["危机加深。"],
                            "conflicts": ["威胁逼近。"],
                            "emotional_beats": ["压力上升。"],
                            "relationship_changes": [],
                            "hook_idea": "更大的麻烦。",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {"title": "开场", "text": _long_scene_text(episode_index=1, title="开场")},
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "hard_pass": True,
                    "hard_errors": [],
                    "soft_scores": {"fidelity": 90},
                    "rewrite_paragraph_indices": [],
                    "rewrite_instructions": "",
                    "fact_digest": "主角出场。",
                    "tone_digest": "紧张。",
                    "state_patch": {},
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {"title": "危机", "text": _long_scene_text(episode_index=2, title="危机")},
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "hard_pass": True,
                    "hard_errors": [],
                    "soft_scores": {"fidelity": 92},
                    "rewrite_paragraph_indices": [],
                    "rewrite_instructions": "",
                    "fact_digest": "危机升级。",
                    "tone_digest": "节奏加快。",
                    "state_patch": {},
                },
                ensure_ascii=False,
            ),
        ]
    )

    # chapter_plan + (draft, critic, commit) x2
    for _ in range(7):
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
        meta = versions.json()[0]["metadata"]
        assert meta["source_kind"] == "novel_to_script"
        assert meta["source_chapter_index"] == 1
        assert meta["chapter_episode_sub_index"] in {1, 2}


async def test_novel_to_script_auto_split_length_too_short_routes_to_fix(client_with_llm_and_embeddings):
    await client_with_llm_and_embeddings.patch(
        "/api/settings/output-spec",
        json={"script_format": "custom"},
    )
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

    short_text = (
        "第1集\n\n"
        "1-1\n日\n内\n地点：杂货铺\n出场人物：主角\n\n"
        "△很短。\n"
    )

    run = await client_with_llm_and_embeddings.post(
        "/api/workflow-runs",
        json={
            "kind": "novel_to_script",
            "brief_snapshot_id": snap_id,
            "split_mode": "auto_by_length",
            "status": "queued",
            "state": {
                "cursor": {
                    "phase": "nts_episode_critic",
                    "chapter_index": 1,
                    "chapter_episode_sub_index": 1,
                    "episode_index": 1,
                },
                "chapter_plan": {
                    "chapter_index": 1,
                    "chapter_title": "第一章：开场",
                    "core_plot": ["主角出场并遭遇危机。"],
                    "episodes": [
                        {
                            "sub_index": 1,
                            "title": "开场",
                            "key_events": ["主角出场。"],
                            "conflicts": ["危机出现。"],
                            "emotional_beats": ["紧张升级。"],
                            "relationship_changes": [],
                            "hook_idea": "危机加深。",
                        }
                    ],
                },
                "draft": {
                    "kind": "episode",
                    "index": 1,
                    "source_chapter_index": 1,
                    "chapter_episode_sub_index": 1,
                    "text": short_text,
                },
                "fix_attempt": 0,
            },
        },
    )
    run_id = run.json()["id"]

    resp = await client_with_llm_and_embeddings.post(f"/api/workflow-runs/{run_id}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["step"]["step_name"] == "nts_episode_critic"
    assert body["run"]["state"]["cursor"]["phase"] == "nts_episode_fix"
    assert body["step"]["outputs"]["hard_pass"] is False
    assert "length_too_short" in body["step"]["outputs"]["hard_errors"]
