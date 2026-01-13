# Change: Add UI for brief/snapshot creation + preferences (global defaults + per-brief overrides)

## Why
The current MVP requires using the API to create Briefs/Snapshots and to set output preferences. To make the product usable as an “IDE”, the UI should support these actions directly and make preference behavior explicit and consistent.

## What Changes
- Add **global default preferences** for `output_spec` (single-user app settings).
- Allow **per-Brief overrides** that inherit from global defaults (override is optional and removable).
- When creating a **Brief Snapshot**, materialize the **effective** `output_spec` (global defaults merged with per-brief overrides) into the snapshot content so workflows remain reproducible.
- Web UI additions:
  - Create Brief (title + optional starter content).
  - Create Snapshot (label).
  - Edit global preferences and per-brief overrides in a dedicated UI section.

## Impact
- Backend:
  - New settings persistence (Postgres) and API endpoints.
  - Brief/output spec schema behavior changes (defaults move to global settings).
  - Snapshot creation resolves effective output spec.
- Frontend:
  - Add “create brief / snapshot” flows.
  - Add global + per-brief preference editor; show effective values.

## Non-Goals (for this change)
- Novel→Script conversion pipeline.
- Change propagation engine and impact graph.
- Multi-user accounts/auth.

