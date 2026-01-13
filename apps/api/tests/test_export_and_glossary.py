from __future__ import annotations


async def test_export_novel_orders_by_ordinal_and_applies_glossary(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    # Glossary: 旧城 -> 新城
    entry = await client.post(
        f"/api/brief-snapshots/{snap_id}/glossary",
        json={"term": "旧城", "replacement": "新城", "metadata": {}},
    )
    assert entry.status_code == 200

    # Create chapters
    ch2 = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 2, "title": "第二章"},
    )
    ch1 = await client.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    assert ch1.status_code == 200
    assert ch2.status_code == 200

    v1 = await client.post(
        f"/api/artifacts/{ch1.json()['id']}/versions",
        json={"source": "agent", "content_text": "他回到旧城。", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    v2 = await client.post(
        f"/api/artifacts/{ch2.json()['id']}/versions",
        json={"source": "agent", "content_text": "她还在旧城。", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert v1.status_code == 200
    assert v2.status_code == 200

    exported = await client.get(f"/api/brief-snapshots/{snap_id}/export/novel.md")
    assert exported.status_code == 200
    text = exported.json()["text"]

    assert text.index("# 第一章") < text.index("# 第二章")
    assert "旧城" not in text
    assert "新城" in text


async def test_export_script_fountain_smoke(client):
    brief = await client.post("/api/briefs", json={"title": "测试剧本", "content": {}})
    brief_id = brief.json()["id"]
    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    snap_id = snap.json()["id"]

    s1 = await client.post(
        "/api/artifacts",
        json={"kind": "script_scene", "ordinal": 1, "title": "第一场"},
    )
    assert s1.status_code == 200

    v1 = await client.post(
        f"/api/artifacts/{s1.json()['id']}/versions",
        json={"source": "agent", "content_text": "INT. 房间 - 夜\n\n主角沉默。", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert v1.status_code == 200

    exported = await client.get(f"/api/brief-snapshots/{snap_id}/export/script.fountain")
    assert exported.status_code == 200
    text = exported.json()["text"]
    assert "== 1. 第一场 ==" in text
    assert "INT. 房间 - 夜" in text

