# Design: Streaming + background workflow execution

## Constraints
- Single-user app, no auth.
- MVP does not require surviving server restarts.
- Keep implementation minimal and debuggable; state remains in DB (`workflow_runs`, `workflow_step_runs`).

## API surface (MVP)
- `POST /api/workflow-runs/{id}/autorun/start` → start background loop for a run
- `POST /api/workflow-runs/{id}/autorun/stop` → stop background loop (does not change run status)
- `GET /api/workflow-runs/{id}/events` → SSE stream of run/step updates

## SSE event model
Use `text/event-stream` with JSON payloads.
Event types (MVP):
- `run` (run updated)
- `step` (step created/updated)
- `log` (optional, for human-readable progress)

## Implementation sketch
- Add an in-process `WorkflowEventHub`:
  - Run-scoped broadcast to multiple subscribers.
  - Each subscriber gets an `asyncio.Queue`.
- Autorun:
  - Store `asyncio.Task` handles per `run_id` in `app.state`.
  - Loop: call the existing `execute_next` endpoint/service until terminal status, paused, or stop requested.
  - Publish events after each step/run update.

## Backwards compatibility
- The existing `POST /api/workflow-runs/{id}/next` remains supported.
- UI can keep “manual next step” as a fallback.

