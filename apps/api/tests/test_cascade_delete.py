from __future__ import annotations

import json
import uuid

import asyncpg


def _asyncpg_url(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+asyncpg://", "postgresql://")


async def _insert_kg_rows(
    *, test_database_url: str, snapshot_id: str, artifact_version_id: str
) -> None:
    conn = await asyncpg.connect(_asyncpg_url(test_database_url))
    try:
        snap = uuid.UUID(snapshot_id)
        version = uuid.UUID(artifact_version_id)

        ent_a = uuid.uuid4()
        ent_b = uuid.uuid4()
        rel_id = uuid.uuid4()
        event_id = uuid.uuid4()

        await conn.execute(
            """
            INSERT INTO kg_entities (id, brief_snapshot_id, name, entity_type, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            ent_a,
            snap,
            "主角",
            "character",
            json.dumps({}),
        )
        await conn.execute(
            """
            INSERT INTO kg_entities (id, brief_snapshot_id, name, entity_type, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            ent_b,
            snap,
            "线索",
            "object",
            json.dumps({}),
        )
        await conn.execute(
            """
            INSERT INTO kg_relations (id, brief_snapshot_id, subject_entity_id, predicate, object_entity_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            rel_id,
            snap,
            ent_a,
            "found",
            ent_b,
            json.dumps({}),
        )
        await conn.execute(
            """
            INSERT INTO kg_events (id, brief_snapshot_id, event_key, summary, time_hint, artifact_version_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            event_id,
            snap,
            None,
            "主角发现线索。",
            None,
            version,
            json.dumps({}),
        )
    finally:
        await conn.close()


async def _insert_brief_message(*, test_database_url: str, brief_id: str) -> None:
    conn = await asyncpg.connect(_asyncpg_url(test_database_url))
    try:
        await conn.execute(
            """
            INSERT INTO brief_messages (id, brief_id, role, content_text, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.uuid4(),
            uuid.UUID(brief_id),
            "user",
            "测试消息",
            json.dumps({"mode": "novel"}),
        )
    finally:
        await conn.close()


async def _counts(*, test_database_url: str) -> dict[str, int]:
    conn = await asyncpg.connect(_asyncpg_url(test_database_url))
    try:
        row = await conn.fetchrow(
            """
            SELECT
              (SELECT count(*) FROM briefs) AS briefs,
              (SELECT count(*) FROM brief_snapshots) AS snapshots,
              (SELECT count(*) FROM brief_messages) AS brief_messages,
              (SELECT count(*) FROM workflow_runs) AS workflow_runs,
              (SELECT count(*) FROM workflow_step_runs) AS workflow_step_runs,
              (SELECT count(*) FROM artifacts) AS artifacts,
              (SELECT count(*) FROM artifact_versions) AS artifact_versions,
              (SELECT count(*) FROM memory_chunks) AS memory_chunks,
              (SELECT count(*) FROM kg_entities) AS kg_entities,
              (SELECT count(*) FROM kg_relations) AS kg_relations,
              (SELECT count(*) FROM kg_events) AS kg_events,
              (SELECT count(*) FROM lint_issues) AS lint_issues,
              (SELECT count(*) FROM lint_issues WHERE artifact_version_id IS NOT NULL) AS lint_issues_ref,
              (SELECT count(*) FROM propagation_events) AS propagation_events,
              (SELECT count(*) FROM artifact_impacts) AS artifact_impacts,
              (SELECT count(*) FROM open_threads) AS open_threads,
              (SELECT count(*) FROM open_thread_refs) AS open_thread_refs,
              (SELECT count(*) FROM snapshot_glossary_entries) AS glossary
            """
        )
        return {k: int(row[k]) for k in row.keys()}
    finally:
        await conn.close()


async def _setup_minimal_graph(
    client,
    *,
    create_duplicate_ordinal: bool = True,
    create_script_scene_issue: bool = True,
) -> dict[str, str]:
    brief = await client.post("/api/briefs", json={"title": "删除测试", "content": {}})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    assert snap.status_code == 200
    snap_id = snap.json()["id"]

    run = await client.post(
        "/api/workflow-runs",
        json={"kind": "novel", "brief_snapshot_id": snap_id, "status": "queued", "state": {}},
    )
    assert run.status_code == 200
    run_id = run.json()["id"]

    step = await client.post(
        f"/api/workflow-runs/{run_id}/steps",
        json={"step_name": "seed", "step_index": 0, "status": "succeeded", "outputs": {}},
    )
    assert step.status_code == 200

    ch1 = await client.post(
        "/api/artifacts", json={"kind": "novel_chapter", "title": "第1章", "ordinal": 1}
    )
    ch2 = await client.post(
        "/api/artifacts", json={"kind": "novel_chapter", "title": "第2章", "ordinal": 2}
    )
    assert ch1.status_code == 200 and ch2.status_code == 200
    ch1_id = ch1.json()["id"]
    ch2_id = ch2.json()["id"]

    base_v1 = await client.post(
        f"/api/artifacts/{ch1_id}/versions",
        json={
            "source": "agent",
            "content_text": "第一章内容。",
            "metadata": {"chapter_index": 1},
            "workflow_run_id": run_id,
            "brief_snapshot_id": snap_id,
        },
    )
    assert base_v1.status_code == 200
    base_v1_id = base_v1.json()["id"]

    v2 = await client.post(
        f"/api/artifacts/{ch2_id}/versions",
        json={
            "source": "agent",
            "content_text": "第二章内容。",
            "metadata": {"chapter_index": 2},
            "workflow_run_id": run_id,
            "brief_snapshot_id": snap_id,
        },
    )
    assert v2.status_code == 200
    v2_id = v2.json()["id"]

    user_edit = await client.post(
        f"/api/artifacts/{ch1_id}/versions",
        json={
            "source": "user",
            "content_text": "第一章（用户修改版）。",
            "metadata": {"edited_from_version_id": base_v1_id},
            "brief_snapshot_id": snap_id,
        },
    )
    assert user_edit.status_code == 200
    user_edit_id = user_edit.json()["id"]

    if create_duplicate_ordinal:
        dup = await client.post(
            "/api/artifacts", json={"kind": "novel_chapter", "title": "重复第1章", "ordinal": 1}
        )
        assert dup.status_code == 200
        dup_id = dup.json()["id"]
        dup_v = await client.post(
            f"/api/artifacts/{dup_id}/versions",
            json={
                "source": "agent",
                "content_text": "重复内容。",
                "metadata": {},
                "workflow_run_id": run_id,
                "brief_snapshot_id": snap_id,
            },
        )
        assert dup_v.status_code == 200

    script_version_id = None
    if create_script_scene_issue:
        scene = await client.post(
            "/api/artifacts", json={"kind": "script_scene", "title": "S1", "ordinal": 1}
        )
        assert scene.status_code == 200
        scene_id = scene.json()["id"]
        scene_v = await client.post(
            f"/api/artifacts/{scene_id}/versions",
            json={
                "source": "agent",
                "content_text": "没有 INT/EXT 标题行的场景。",
                "metadata": {},
                "workflow_run_id": run_id,
                "brief_snapshot_id": snap_id,
            },
        )
        assert scene_v.status_code == 200
        script_version_id = scene_v.json()["id"]

    # Propagation: base (agent) -> edited (user), impacts downstream chapter.
    applied = await client.post(
        f"/api/brief-snapshots/{snap_id}/propagation/apply",
        params={"use_llm": "false"},
        json={"base_artifact_version_id": base_v1_id, "edited_artifact_version_id": user_edit_id},
    )
    assert applied.status_code == 200
    assert len(applied.json().get("impacts") or []) >= 1

    thread = await client.post(
        f"/api/brief-snapshots/{snap_id}/threads",
        json={"title": "伏笔", "description": "测试", "status": "open"},
    )
    assert thread.status_code == 200
    thread_id = thread.json()["id"]

    ref = await client.post(
        f"/api/brief-snapshots/{snap_id}/threads/{thread_id}/refs",
        json={"artifact_version_id": base_v1_id, "ref_kind": "introduced", "quote": "第一章内容"},
    )
    assert ref.status_code == 200

    gloss = await client.post(
        f"/api/brief-snapshots/{snap_id}/glossary",
        json={"term": "旧城", "replacement": "新城"},
    )
    assert gloss.status_code == 200

    lint = await client.post(
        f"/api/brief-snapshots/{snap_id}/lint",
        params={"use_llm": "false"},
        json={},
    )
    assert lint.status_code == 200

    return {
        "brief_id": brief_id,
        "snapshot_id": snap_id,
        "run_id": run_id,
        "base_version_id": base_v1_id,
        "user_version_id": user_edit_id,
        "downstream_version_id": v2_id,
        "script_version_id": script_version_id,
    }


async def test_delete_workflow_run_cascades(client_with_llm_and_embeddings, test_database_url):
    ids = await _setup_minimal_graph(client_with_llm_and_embeddings)
    await _insert_kg_rows(
        test_database_url=test_database_url,
        snapshot_id=ids["snapshot_id"],
        artifact_version_id=ids["base_version_id"],
    )

    before = await _counts(test_database_url=test_database_url)
    assert before["workflow_runs"] == 1
    assert before["workflow_step_runs"] >= 1
    assert before["artifact_versions"] >= 4
    assert before["memory_chunks"] >= 4
    assert before["open_thread_refs"] == 1
    assert before["propagation_events"] == 1
    assert before["artifact_impacts"] >= 1
    assert before["kg_events"] == 1

    deleted = await client_with_llm_and_embeddings.delete(f"/api/workflow-runs/{ids['run_id']}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    after = await _counts(test_database_url=test_database_url)
    assert after["briefs"] == 1
    assert after["snapshots"] == 1
    assert after["workflow_runs"] == 0
    assert after["workflow_step_runs"] == 0
    assert after["propagation_events"] == 0
    assert after["artifact_impacts"] == 0
    assert after["open_threads"] == 1
    assert after["open_thread_refs"] == 0
    assert after["kg_events"] == 0
    assert after["lint_issues_ref"] == 0

    # Only the user edit version remains (agent-produced versions were deleted with the run).
    assert after["artifact_versions"] == 1
    assert after["memory_chunks"] == 1
    assert after["artifacts"] == 1


async def test_delete_brief_snapshot_cascades(client_with_llm_and_embeddings, test_database_url):
    ids = await _setup_minimal_graph(client_with_llm_and_embeddings)
    await _insert_kg_rows(
        test_database_url=test_database_url,
        snapshot_id=ids["snapshot_id"],
        artifact_version_id=ids["base_version_id"],
    )

    before = await _counts(test_database_url=test_database_url)
    assert before["snapshots"] == 1
    assert before["workflow_runs"] == 1
    assert before["artifact_versions"] >= 4
    assert before["memory_chunks"] >= 4
    assert before["open_threads"] == 1
    assert before["open_thread_refs"] == 1
    assert before["propagation_events"] == 1
    assert before["artifact_impacts"] >= 1
    assert before["kg_entities"] >= 2
    assert before["kg_relations"] >= 1
    assert before["kg_events"] == 1
    assert before["glossary"] == 1

    deleted = await client_with_llm_and_embeddings.delete(
        f"/api/brief-snapshots/{ids['snapshot_id']}"
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    after = await _counts(test_database_url=test_database_url)
    assert after["briefs"] == 1
    assert after["snapshots"] == 0
    assert after["workflow_runs"] == 0
    assert after["workflow_step_runs"] == 0
    assert after["artifact_versions"] == 0
    assert after["memory_chunks"] == 0
    assert after["artifacts"] == 0
    assert after["kg_entities"] == 0
    assert after["kg_relations"] == 0
    assert after["kg_events"] == 0
    assert after["lint_issues"] == 0
    assert after["propagation_events"] == 0
    assert after["artifact_impacts"] == 0
    assert after["open_threads"] == 0
    assert after["open_thread_refs"] == 0
    assert after["glossary"] == 0


async def test_delete_brief_cascades(client_with_llm_and_embeddings, test_database_url):
    ids = await _setup_minimal_graph(client_with_llm_and_embeddings)
    await _insert_kg_rows(
        test_database_url=test_database_url,
        snapshot_id=ids["snapshot_id"],
        artifact_version_id=ids["base_version_id"],
    )
    await _insert_brief_message(test_database_url=test_database_url, brief_id=ids["brief_id"])

    before = await _counts(test_database_url=test_database_url)
    assert before["briefs"] == 1
    assert before["snapshots"] == 1
    assert before["brief_messages"] == 1

    deleted = await client_with_llm_and_embeddings.delete(f"/api/briefs/{ids['brief_id']}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    after = await _counts(test_database_url=test_database_url)
    assert after["briefs"] == 0
    assert after["snapshots"] == 0
    assert after["brief_messages"] == 0
    assert after["workflow_runs"] == 0
    assert after["workflow_step_runs"] == 0
    assert after["artifact_versions"] == 0
    assert after["memory_chunks"] == 0
    assert after["artifacts"] == 0
    assert after["kg_entities"] == 0
    assert after["kg_relations"] == 0
    assert after["kg_events"] == 0
    assert after["lint_issues"] == 0
    assert after["propagation_events"] == 0
    assert after["artifact_impacts"] == 0
    assert after["open_threads"] == 0
    assert after["open_thread_refs"] == 0
    assert after["glossary"] == 0
