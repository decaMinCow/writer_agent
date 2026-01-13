# Change: Add streaming + background workflow execution (SSE)

## Why
The current workflow execution model is “click next” (or UI polling loops), which makes long runs fragile and hard to observe. We need:
- Real-time progress updates in the IDE (without polling).
- A single action to run until completion (“autorun”) while still producing step-by-step artifacts.

The user has confirmed we do **not** need persistence across API restarts for MVP.

## What Changes
- Backend:
  - Add an in-process **autorun loop** per workflow run (start/pause/cancel).
  - Add **SSE** endpoint to stream workflow run/step updates to the UI.
- Frontend:
  - Subscribe to SSE for the selected run and render live progress/logs.
  - Replace the current tight client-side loop with server-driven autorun.

## Impact
- Affected specs: `execute-workflows`, `web-ui`
- Affected code:
  - Backend: `apps/api/app/api/routers/workflows.py` (+ new small services)
  - Frontend: `apps/web/src/routes/+page.svelte`, `apps/web/src/lib/api.ts`

## Non-Goals (for this change)
- Durable job queue, resuming autorun after restarts
- WebSocket support (SSE is the MVP transport)
- Multi-user auth or per-user event isolation

