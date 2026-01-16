from __future__ import annotations

import json


async def test_rebuild_knowledge_graph_indexes_entities_relations_events(client_with_llm, llm_stub):
    brief = await client_with_llm.post("/api/briefs", json={"title": "测试作品", "content": {}})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    assert snap.status_code == 200
    snap_id = snap.json()["id"]

    artifact = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    assert artifact.status_code == 200
    artifact_id = artifact.json()["id"]

    version = await client_with_llm.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={
            "source": "agent",
            "content_text": "第一章内容",
            "metadata": {"fact_digest": "第一章：阿澄来到旧城。", "tone_digest": "冷峻、克制"},
            "brief_snapshot_id": snap_id,
        },
    )
    assert version.status_code == 200
    version_id = version.json()["id"]

    llm_stub.outputs.append(
        json.dumps(
            {
                "entities": [
                    {"name": "阿澄", "entity_type": "person", "metadata": {"aliases": ["阿澄"]}},
                    {"name": "旧城", "entity_type": "location", "metadata": {}},
                ],
                "relations": [
                    {
                        "subject": "阿澄",
                        "subject_type": "person",
                        "predicate": "located_in",
                        "object": "旧城",
                        "object_type": "location",
                        "metadata": {},
                    }
                ],
                "events": [
                    {
                        "event_key": "ch1_e01",
                        "summary": "阿澄来到旧城。",
                        "time_hint": "清晨",
                        "metadata": {},
                    }
                ],
            },
            ensure_ascii=False,
        )
    )

    rebuilt = await client_with_llm.post(f"/api/brief-snapshots/{snap_id}/kg/rebuild")
    assert rebuilt.status_code == 200
    assert rebuilt.json() == {
        "entities_indexed": 2,
        "relations_indexed": 1,
        "events_indexed": 1,
    }

    kg = await client_with_llm.get(f"/api/brief-snapshots/{snap_id}/kg")
    assert kg.status_code == 200
    data = kg.json()
    assert len(data["entities"]) == 2
    assert len(data["relations"]) == 1
    assert len(data["events"]) == 1

    entity_ids = {item["id"] for item in data["entities"]}
    assert data["relations"][0]["predicate"] == "located_in"
    assert data["relations"][0]["subject_entity_id"] in entity_ids
    assert data["relations"][0]["object_entity_id"] in entity_ids

    assert data["events"][0]["event_key"] == "ch1_e01"
    assert data["events"][0]["artifact_version_id"] == version_id


async def test_story_linter_duplicate_ordinals_produces_hard_issue(client_with_llm):
    brief = await client_with_llm.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    a1 = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    a2 = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章（重复）"},
    )
    assert a1.status_code == 200
    assert a2.status_code == 200

    v1 = await client_with_llm.post(
        f"/api/artifacts/{a1.json()['id']}/versions",
        json={"source": "agent", "content_text": "内容1", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    v2 = await client_with_llm.post(
        f"/api/artifacts/{a2.json()['id']}/versions",
        json={"source": "agent", "content_text": "内容2", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert v1.status_code == 200
    assert v2.status_code == 200

    run = await client_with_llm.post(
        f"/api/brief-snapshots/{snap_id}/lint",
        params={"use_llm": "false"},
    )
    assert run.status_code == 200
    issues = run.json()["issues"]
    assert any(item["code"] == "duplicate_artifact_ordinal" and item["severity"] == "hard" for item in issues)

    listed = await client_with_llm.get(f"/api/brief-snapshots/{snap_id}/lint")
    assert listed.status_code == 200
    assert any(item["code"] == "duplicate_artifact_ordinal" for item in listed.json())


async def test_story_linter_missing_int_ext_heading_produces_soft_issue(client_with_llm):
    await client_with_llm.patch(
        "/api/settings/output-spec",
        json={"script_format": "screenplay_int_ext"},
    )
    brief = await client_with_llm.post(
        "/api/briefs",
        json={"title": "测试作品", "content": {"output_spec": {"script_format": "screenplay_int_ext"}}},
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    scene = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "script_scene", "ordinal": 1, "title": "第一场"},
    )
    assert scene.status_code == 200
    scene_id = scene.json()["id"]

    created = await client_with_llm.post(
        f"/api/artifacts/{scene_id}/versions",
        json={
            "source": "agent",
            "content_text": "第一场\n阿澄走进小巷。",
            "metadata": {},
            "brief_snapshot_id": snap_id,
        },
    )
    assert created.status_code == 200
    version_id = created.json()["id"]

    run = await client_with_llm.post(
        f"/api/brief-snapshots/{snap_id}/lint",
        params={"use_llm": "false"},
    )
    assert run.status_code == 200
    issues = run.json()["issues"]
    assert any(
        item["code"] == "missing_int_ext_heading" and item["artifact_version_id"] == version_id
        for item in issues
    )


async def test_story_linter_can_include_llm_issues(client_with_llm, llm_stub):
    llm_stub.outputs.append(
        json.dumps(
            {
                "issues": [
                    {
                        "severity": "soft",
                        "code": "pov_drift",
                        "message": "疑似视角漂移：建议统一为第三人称有限。",
                        "artifact_version_id": None,
                        "metadata": {"recommended_pov": "third_limited"},
                    }
                ]
            },
            ensure_ascii=False,
        )
    )

    await client_with_llm.patch(
        "/api/settings/output-spec",
        json={"script_format": "stage_play"},
    )
    brief = await client_with_llm.post(
        "/api/briefs",
        json={"title": "测试作品", "content": {"output_spec": {"script_format": "stage_play"}}},
    )
    brief_id = brief.json()["id"]
    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    artifact = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    assert artifact.status_code == 200
    artifact_id = artifact.json()["id"]

    created = await client_with_llm.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={"source": "agent", "content_text": "内容", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert created.status_code == 200

    run = await client_with_llm.post(f"/api/brief-snapshots/{snap_id}/lint", params={"use_llm": "true"})
    assert run.status_code == 200
    issues = run.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["code"] == "pov_drift"
    assert issues[0]["metadata"]["recommended_pov"] == "third_limited"
