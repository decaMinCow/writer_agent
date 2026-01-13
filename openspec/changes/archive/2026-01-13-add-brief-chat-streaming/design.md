# Design: Streaming brief chat (SSE over fetch)

## Endpoint
Add `POST /api/briefs/{brief_id}/messages/stream` returning `text/event-stream`.

Events:
- `assistant_delta`: `{ "append": "<text>" }` incremental assistant text (best-effort; extracted from the LLM JSON stream).
- `final`: `{ "brief": ..., "gap_report": ..., "messages": [...] }` same payload as non-stream `POST /messages`.
- `error`: `{ "detail": "<reason>" }`

## LLM output + delta extraction
The Brief Builder prompt is structured JSON. For streaming UX, the backend:
- Requests a streaming chat completion.
- Accumulates the raw JSON output for final parsing/validation.
- Extracts the `assistant_message` string incrementally (requires the model to emit `assistant_message` first) and emits `assistant_delta` events.

At stream end, the backend validates the JSON payload and performs the same DB updates as the non-stream endpoint, then emits a `final` event.

## Frontend
The web app uses `fetch()` with a streaming response body (SSE parsing) because browser `EventSource` does not support POST.
- Optimistically appends the user message to the chat list.
- Adds a temporary assistant message updated by `assistant_delta`.
- Replaces state with the `final` payload after completion.

## Fallback
If the resolved LLM client does not support streaming (e.g., test stubs), the endpoint emits only a `final` event.

