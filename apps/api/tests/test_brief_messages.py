from __future__ import annotations

import json


async def test_post_brief_message_updates_brief_and_stores_messages(client_with_llm, llm_stub):
    llm_stub.outputs.append(
        json.dumps(
            {
                "assistant_message": "好的，我先补充一句话卖点，并给你追问几个关键点。",
                "brief_patch": {"content": {"logline": "一名实习编辑卷入连环失踪案。"}, "title": "失踪编辑"},
                "gap_report": {
                    "mode": "novel",
                    "confirmed": ["title", "logline"],
                    "pending": [],
                    "missing": ["characters.main", "world.rules"],
                    "conflict": [],
                    "questions": ["主角是谁？他/她最想要什么？", "故事发生在哪个城市/时代？"],
                    "completeness": 30,
                },
            },
            ensure_ascii=False,
        )
    )

    brief = await client_with_llm.post("/api/briefs", json={"title": "测试作品"})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]

    resp = await client_with_llm.post(
        f"/api/briefs/{brief_id}/messages",
        json={"content_text": "我想写一个都市悬疑", "mode": "novel"},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["brief"]["title"] == "失踪编辑"
    assert body["brief"]["content"]["logline"] == "一名实习编辑卷入连环失踪案。"
    assert body["gap_report"]["mode"] == "novel"
    assert body["gap_report"]["completeness"] == 30

    messages = body["messages"]
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content_text"] == "我想写一个都市悬疑"
    assert messages[0]["metadata"]["mode"] == "novel"
    assert messages[-1]["role"] == "assistant"


async def test_post_brief_message_repairs_invalid_json(client_with_llm, llm_stub):
    llm_stub.outputs.append("```json\n{ not valid json }\n```")
    llm_stub.outputs.append(
        json.dumps(
            {
                "assistant_message": "已修复输出并更新简报。",
                "brief_patch": {"content": {"genres": ["悬疑"]}},
                "gap_report": {
                    "mode": "novel",
                    "confirmed": ["genres"],
                    "pending": [],
                    "missing": [],
                    "conflict": [],
                    "questions": [],
                    "completeness": 100,
                },
            },
            ensure_ascii=False,
        )
    )

    brief = await client_with_llm.post("/api/briefs", json={"title": "测试作品"})
    brief_id = brief.json()["id"]

    resp = await client_with_llm.post(
        f"/api/briefs/{brief_id}/messages",
        json={"content_text": "类型就按悬疑", "mode": "novel"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["brief"]["content"]["genres"] == ["悬疑"]
    assert len(llm_stub.calls) == 2


async def test_post_brief_message_requires_openai_config(client):
    brief = await client.post("/api/briefs", json={"title": "测试作品"})
    brief_id = brief.json()["id"]

    resp = await client.post(
        f"/api/briefs/{brief_id}/messages",
        json={"content_text": "我想写一个都市悬疑", "mode": "novel"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "openai_not_configured"

