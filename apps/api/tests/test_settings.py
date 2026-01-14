from __future__ import annotations


async def test_output_spec_defaults_get_and_patch(client):
    got = await client.get("/api/settings/output-spec")
    assert got.status_code == 200
    body = got.json()
    assert body["language"] == "zh-CN"
    assert body["script_format"] == "screenplay_int_ext"
    assert body["script_format_notes"] is None
    assert body["max_fix_attempts"] == 2
    assert body["auto_step_retries"] == 3
    assert isinstance(body["auto_step_backoff_s"], (int, float))

    patched = await client.patch(
        "/api/settings/output-spec",
        json={
            "language": "en-US",
            "script_format": "stage_play",
            "script_format_notes": "偏舞台剧",
            "max_fix_attempts": 3,
            "auto_step_retries": 7,
            "auto_step_backoff_s": 0.0,
        },
    )
    assert patched.status_code == 200
    patched_body = patched.json()
    assert patched_body["language"] == "en-US"
    assert patched_body["script_format"] == "stage_play"
    assert patched_body["script_format_notes"] == "偏舞台剧"
    assert patched_body["max_fix_attempts"] == 3
    assert patched_body["auto_step_retries"] == 7
    assert patched_body["auto_step_backoff_s"] == 0.0

    got2 = await client.get("/api/settings/output-spec")
    assert got2.status_code == 200
    body2 = got2.json()
    assert body2["language"] == "en-US"
    assert body2["script_format"] == "stage_play"
    assert body2["max_fix_attempts"] == 3
    assert body2["auto_step_retries"] == 7


async def test_snapshot_materializes_effective_output_spec(client):
    await client.patch(
        "/api/settings/output-spec",
        json={
            "language": "en-US",
            "script_format": "stage_play",
            "script_format_notes": None,
            "auto_step_retries": 4,
            "auto_step_backoff_s": 0.0,
        },
    )

    brief = await client.post(
        "/api/briefs",
        json={"title": "测试作品", "content": {"output_spec": {"script_format": "screenplay_int_ext"}}},
    )
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    snap = await client.post(f"/api/briefs/{brief_id}/snapshots", json={"label": "v1"})
    assert snap.status_code == 200
    snap_content = snap.json()["content"]
    assert snap_content["output_spec"]["language"] == "en-US"
    assert snap_content["output_spec"]["script_format"] == "screenplay_int_ext"
    assert snap_content["output_spec"]["max_fix_attempts"] == 2
    assert snap_content["output_spec"]["auto_step_retries"] == 4
    assert snap_content["output_spec"]["auto_step_backoff_s"] == 0.0


async def test_patch_output_spec_can_clear_overrides(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品"})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    patched = await client.patch(
        f"/api/briefs/{brief_id}/output-spec",
        json={"script_format": "stage_play"},
    )
    assert patched.status_code == 200
    assert patched.json()["content"]["output_spec"]["script_format"] == "stage_play"

    cleared = await client.patch(
        f"/api/briefs/{brief_id}/output-spec",
        json={"script_format": None},
    )
    assert cleared.status_code == 200
    assert "script_format" not in cleared.json()["content"]["output_spec"]


async def test_llm_provider_settings_get_and_patch_and_clear(client):
    got = await client.get("/api/settings/llm-provider")
    assert got.status_code == 200
    body = got.json()
    assert "api_key" not in body
    assert body["api_key_configured"] is False
    assert body["model"]  # has env default
    assert body["embeddings_model"]
    assert isinstance(body["timeout_s"], (int, float))
    assert isinstance(body["max_retries"], int)

    patched = await client.patch(
        "/api/settings/llm-provider",
        json={
            "base_url": "https://example.com/v1",
            "model": "gpt-test",
            "embeddings_model": "text-embedding-test",
            "timeout_s": 12,
            "max_retries": 5,
            "api_key": "sk-test",
        },
    )
    assert patched.status_code == 200
    patched_body = patched.json()
    assert "api_key" not in patched_body
    assert patched_body["api_key_configured"] is True
    assert patched_body["base_url"] == "https://example.com/v1"
    assert patched_body["model"] == "gpt-test"
    assert patched_body["embeddings_model"] == "text-embedding-test"
    assert patched_body["timeout_s"] == 12
    assert patched_body["max_retries"] == 5

    cleared = await client.patch("/api/settings/llm-provider", json={"api_key": None})
    assert cleared.status_code == 200
    cleared_body = cleared.json()
    assert "api_key" not in cleared_body
    assert cleared_body["api_key_configured"] is False
