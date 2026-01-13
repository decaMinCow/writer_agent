## 1. Implementation
- [x] Add streaming support in the OpenAI chat client wrapper.
- [x] Add `POST /api/briefs/{brief_id}/messages/stream` SSE endpoint and incremental assistant delta extraction.
- [x] Update Brief Builder prompt to encourage `assistant_message` to be emitted first for better streaming UX.
- [x] Update web UI chat send flow to use streaming endpoint and render deltas.
- [x] Add backend tests that consume SSE and assert `assistant_delta` + `final` behavior.

## 2. Validation
- [x] `openspec validate add-brief-chat-streaming --strict`
- [x] `cd apps/api && uv run pytest`
- [x] `cd apps/web && npm run lint && npm run check`
