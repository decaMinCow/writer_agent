from __future__ import annotations


async def test_propagation_preview_apply_and_repair_flow(client_with_llm, llm_stub):
    brief = await client_with_llm.post("/api/briefs", json={"title": "测试作品", "content": {}})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    snap = await client_with_llm.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    assert snap.status_code == 200
    snap_id = snap.json()["id"]

    ch1 = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 1, "title": "第一章"},
    )
    ch2 = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 2, "title": "第二章"},
    )
    ch3 = await client_with_llm.post(
        "/api/artifacts",
        json={"kind": "novel_chapter", "ordinal": 3, "title": "第三章"},
    )
    assert ch1.status_code == 200
    assert ch2.status_code == 200
    assert ch3.status_code == 200

    ch1_id = ch1.json()["id"]
    ch2_id = ch2.json()["id"]
    ch3_id = ch3.json()["id"]

    v1 = await client_with_llm.post(
        f"/api/artifacts/{ch1_id}/versions",
        json={"source": "agent", "content_text": "第一章：阿澄来到旧城。", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    v2 = await client_with_llm.post(
        f"/api/artifacts/{ch2_id}/versions",
        json={"source": "agent", "content_text": "第二章：她在旧城寻找线索。", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    v3 = await client_with_llm.post(
        f"/api/artifacts/{ch3_id}/versions",
        json={"source": "agent", "content_text": "第三章：她遇到一名陌生人。", "metadata": {}, "brief_snapshot_id": snap_id},
    )
    assert v1.status_code == 200
    assert v2.status_code == 200
    assert v3.status_code == 200

    base_version_id = v1.json()["id"]

    edited = await client_with_llm.post(
        f"/api/artifacts/{ch1_id}/versions",
        json={
            "source": "user",
            "content_text": "第一章：阿澄来到新城。她决定不再回头。",
            "metadata": {"edited_from_version_id": base_version_id},
            "brief_snapshot_id": snap_id,
        },
    )
    assert edited.status_code == 200
    edited_version_id = edited.json()["id"]

    preview = await client_with_llm.post(
        f"/api/brief-snapshots/{snap_id}/propagation/preview",
        json={
            "base_artifact_version_id": base_version_id,
            "edited_artifact_version_id": edited_version_id,
        },
    )
    assert preview.status_code == 200
    preview_data = preview.json()
    assert "文本已修改" in preview_data["fact_changes"]
    assert len(preview_data["impacts"]) == 2
    impacted_ids = {item["artifact_id"] for item in preview_data["impacts"]}
    assert ch2_id in impacted_ids
    assert ch3_id in impacted_ids

    applied = await client_with_llm.post(
        f"/api/brief-snapshots/{snap_id}/propagation/apply",
        json={
            "base_artifact_version_id": base_version_id,
            "edited_artifact_version_id": edited_version_id,
        },
    )
    assert applied.status_code == 200
    event_id = applied.json()["event"]["id"]
    assert len(applied.json()["impacts"]) == 2

    impacts = await client_with_llm.get(f"/api/brief-snapshots/{snap_id}/impacts")
    assert impacts.status_code == 200
    assert len(impacts.json()) == 2

    llm_stub.outputs.append("第二章（修复后）：她在新城寻找线索。")
    llm_stub.outputs.append("第三章（修复后）：她在新城遇到一名陌生人。")

    repaired = await client_with_llm.post(
        f"/api/brief-snapshots/{snap_id}/propagation/events/{event_id}/repair",
        json={},
    )
    assert repaired.status_code == 200
    repaired_data = repaired.json()
    assert len(repaired_data["repaired"]) == 2
    assert all(item["repaired_artifact_version_id"] for item in repaired_data["impacts"])

    impacts_after = await client_with_llm.get(f"/api/brief-snapshots/{snap_id}/impacts")
    assert impacts_after.status_code == 200
    assert impacts_after.json() == []

    versions2 = await client_with_llm.get(f"/api/artifacts/{ch2_id}/versions")
    assert versions2.status_code == 200
    assert any(v["content_text"].startswith("第二章（修复后）") for v in versions2.json())

