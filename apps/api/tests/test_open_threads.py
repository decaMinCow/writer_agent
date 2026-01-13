from __future__ import annotations


async def test_open_threads_crud_and_reference_linking(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品", "content": {}})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    assert snap.status_code == 200
    snap_id = snap.json()["id"]

    created = await client.post(
        f"/api/brief-snapshots/{snap_id}/threads",
        json={"title": "线索：神秘戒指", "description": "主角在第一章捡到一枚戒指。", "status": "open", "metadata": {}},
    )
    assert created.status_code == 200
    thread_id = created.json()["id"]
    assert created.json()["status"] == "open"

    listed = await client.get(f"/api/brief-snapshots/{snap_id}/threads")
    assert listed.status_code == 200
    assert any(item["id"] == thread_id for item in listed.json())

    closed = await client.patch(
        f"/api/brief-snapshots/{snap_id}/threads/{thread_id}",
        json={"status": "closed"},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    artifact = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    assert artifact.status_code == 200
    artifact_id = artifact.json()["id"]

    version = await client.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={"source": "agent", "content_text": "第一章内容", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert version.status_code == 200
    version_id = version.json()["id"]

    ref = await client.post(
        f"/api/brief-snapshots/{snap_id}/threads/{thread_id}/refs",
        json={"artifact_version_id": version_id, "ref_kind": "introduced", "quote": "戒指冰冷。", "metadata": {}},
    )
    assert ref.status_code == 200
    assert ref.json()["artifact_version_id"] == version_id

    refs = await client.get(f"/api/brief-snapshots/{snap_id}/threads/{thread_id}/refs")
    assert refs.status_code == 200
    assert len(refs.json()) == 1


async def test_open_thread_ref_rejects_cross_snapshot_link(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]

    snap1 = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap2 = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v2"})
    snap1_id = snap1.json()["id"]
    snap2_id = snap2.json()["id"]

    thread = await client.post(
        f"/api/brief-snapshots/{snap1_id}/threads",
        json={"title": "线索：钥匙", "description": None, "status": "open", "metadata": {}},
    )
    thread_id = thread.json()["id"]

    artifact = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    artifact_id = artifact.json()["id"]

    version = await client.post(
        f"/api/artifacts/{artifact_id}/versions",
        json={"source": "agent", "content_text": "第一章内容", "metadata": {}, "brief_snapshot_id": snap2_id},
    )
    version_id = version.json()["id"]

    ref = await client.post(
        f"/api/brief-snapshots/{snap1_id}/threads/{thread_id}/refs",
        json={"artifact_version_id": version_id, "ref_kind": "introduced", "quote": None, "metadata": {}},
    )
    assert ref.status_code == 400
    assert ref.json()["detail"] == "artifact_version_not_in_snapshot"

