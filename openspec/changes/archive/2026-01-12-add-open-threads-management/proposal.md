# Change: Add Open Threads (foreshadowing) management

## Why
Open Threads (伏笔/线索/悬念) are essential for long-form consistency. We need a first-class way to track threads, attach them to chapters/scenes, and mark them resolved.

## What Changes
- Backend:
  - Add snapshot-scoped Open Threads tables and APIs (CRUD + status + references).
- Frontend:
  - Add an “Open Threads” panel to view open/closed threads and jump to referenced artifacts/versions.

## Impact
- Affected specs (new): `open-threads`
- Affected specs (update): `web-ui`
- Affected code: DB migrations, new API router, IDE UI panel

## Non-Goals (for this change)
- Fully automatic thread extraction from prose (can be added later)
- Advanced graph visualization of thread dependencies

