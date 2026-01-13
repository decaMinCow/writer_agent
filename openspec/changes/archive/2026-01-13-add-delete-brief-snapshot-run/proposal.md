# Change: Delete Brief / Snapshot / Workflow Run (cascade) + Hierarchy UI

## Why
The IDE currently accumulates generated data (briefs, snapshots, workflow runs, artifacts, memory/KG/lint, etc.) with no way to delete old or test content. This makes it hard to manage multiple projects and keep the workspace clean.

## What Changes
- Add destructive delete actions for:
  - Brief
  - Brief Snapshot (“版本”)
  - Workflow Run
- Ensure deletions are **cascading**: deleting a parent removes all contained/derived records (artifacts, versions, memory chunks, KG/lint, propagation, open threads, glossary, step history).
- Improve UI hierarchy:
  - Select Brief → show only its Snapshots
  - Select Snapshot → show only its Workflow Runs
- Show Workflow Runs with **Chinese, phase-aware** display names (based on workflow kind + cursor phase/index).

## Impact
- Affected specs:
  - `manage-briefs`
  - `brief-snapshots`
  - `run-workflows`
  - `web-ui`
- Affected code:
  - Backend: new DELETE endpoints + cascade delete service + tests
  - Frontend: hierarchy filtering + delete buttons + run display naming

## Non-Goals (for this change)
- No auth / multi-user permissions (single-user mode remains).
- No “trash bin” / undo for deletes (hard delete only; confirmation in UI).

