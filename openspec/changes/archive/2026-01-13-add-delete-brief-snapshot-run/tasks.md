## 1. Spec + Validation
- [x] Draft delta specs for delete + hierarchy UI
- [x] Run `openspec validate add-delete-brief-snapshot-run --strict` and fix all issues

## 2. Backend (FastAPI)
- [x] Add cascade delete service for brief/snapshot/run
- [x] Add `DELETE /api/briefs/{brief_id}` (cascade)
- [x] Add `DELETE /api/brief-snapshots/{snapshot_id}` (cascade)
- [x] Add `DELETE /api/workflow-runs/{run_id}` (cascade)
- [x] Ensure deleting a run stops autorun tasks (best-effort)

## 3. Frontend (SvelteKit)
- [x] Add API client helpers for the new DELETE endpoints
- [x] Update UI hierarchy:
  - [x] Selecting a Brief shows only its snapshots
  - [x] Selecting a Snapshot shows only its workflow runs
- [x] Add delete buttons with confirmation for Brief / Snapshot / Run
- [x] Show run list items with phase-aware Chinese display names

## 4. Tests
- [x] Add API tests covering cascade deletion for run/snapshot/brief
- [x] Verify orphan artifacts are cleaned up (no versions remain)

## 5. Verification + Cleanup
- [x] Run backend tests (`cd apps/api && uv run pytest`) and fix any failures introduced by this change
- [x] Run frontend typecheck (`cd apps/web && npm run check`)
- [x] Mark all tasks complete in this file after implementation
