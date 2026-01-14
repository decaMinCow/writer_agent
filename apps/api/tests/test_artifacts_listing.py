from __future__ import annotations


async def test_list_artifacts_can_filter_by_snapshot(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap1 = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap2 = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v2"})
    snap1_id = snap1.json()["id"]
    snap2_id = snap2.json()["id"]

    only_1 = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "只在 v1"},
    )
    only_2 = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 2, "title": "只在 v2"},
    )
    both = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 3, "title": "两边都有"},
    )
    a1_id = only_1.json()["id"]
    a2_id = only_2.json()["id"]
    both_id = both.json()["id"]

    await client.post(
        f"/api/artifacts/{a1_id}/versions",
        json={"source": "agent", "content_text": "v1 内容", "metadata": {}, "brief_snapshot_id": snap1_id},
    )
    await client.post(
        f"/api/artifacts/{a2_id}/versions",
        json={"source": "agent", "content_text": "v2 内容", "metadata": {}, "brief_snapshot_id": snap2_id},
    )
    await client.post(
        f"/api/artifacts/{both_id}/versions",
        json={"source": "agent", "content_text": "v1 共同内容", "metadata": {}, "brief_snapshot_id": snap1_id},
    )
    await client.post(
        f"/api/artifacts/{both_id}/versions",
        json={"source": "agent", "content_text": "v2 共同内容", "metadata": {}, "brief_snapshot_id": snap2_id},
    )

    all_items = await client.get("/api/artifacts")
    assert all_items.status_code == 200
    all_ids = {item["id"] for item in all_items.json()}
    assert all_ids == {a1_id, a2_id, both_id}

    only_v1 = await client.get("/api/artifacts", params={"brief_snapshot_id": snap1_id})
    assert only_v1.status_code == 200
    v1_ids = {item["id"] for item in only_v1.json()}
    assert v1_ids == {a1_id, both_id}

    only_v2 = await client.get("/api/artifacts", params={"brief_snapshot_id": snap2_id})
    assert only_v2.status_code == 200
    v2_ids = {item["id"] for item in only_v2.json()}
    assert v2_ids == {a2_id, both_id}

    v1_versions = await client.get(
        f"/api/artifacts/{both_id}/versions",
        params={"brief_snapshot_id": snap1_id},
    )
    assert v1_versions.status_code == 200
    versions = v1_versions.json()
    assert len(versions) == 1
    assert versions[0]["brief_snapshot_id"] == snap1_id

