## 1. Backend
- [x] Add `POST /api/brief-snapshots/{snapshot_id}/lint/repair` to batch-fix lint issues that have `artifact_version_id`.
- [x] Implement safe limits (max items) and return summary (created versions, skipped issues).
- [x] Add tests covering repair flow and version creation.

## 2. Frontend
- [x] Add “一键修复（创建新版本）” action in the lint panel.
- [x] Show repair result summary and guide user to rerun lint.

## 3. Validation
- [x] Run `openspec validate add-lint-one-click-repair --strict`.
- [x] Run `cd apps/api && uv run pytest -q` and `cd apps/web && npm run check`.
