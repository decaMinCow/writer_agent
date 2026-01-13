from __future__ import annotations


async def test_create_brief_and_snapshot_order(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品"})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    snap1 = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    assert snap1.status_code == 200

    snap2 = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v2"})
    assert snap2.status_code == 200

    snaps = await client.get(f"/api/briefs/{brief_id}/snapshots")
    assert snaps.status_code == 200
    data = snaps.json()
    assert [item["label"] for item in data] == ["v2", "v1"]


async def test_patch_script_format_independently(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品"})
    brief_id = brief.json()["id"]

    patched = await client.patch(
        f"/api/briefs/{brief_id}/output-spec",
        json={"script_format": "stage_play", "script_format_notes": "偏舞台剧格式"},
    )
    assert patched.status_code == 200
    content = patched.json()["content"]
    assert content["output_spec"]["script_format"] == "stage_play"
    assert content["output_spec"]["script_format_notes"] == "偏舞台剧格式"
