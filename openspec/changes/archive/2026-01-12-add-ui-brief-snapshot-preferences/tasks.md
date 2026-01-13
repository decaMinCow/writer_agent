## 1. Implementation
- [x] 1.1 Add `app_settings` table + SQLAlchemy model + Alembic migration
- [x] 1.2 Add backend endpoints for global `output_spec` defaults (get/patch)
- [x] 1.3 Update brief schemas so `output_spec` supports overrides (no per-brief defaults)
- [x] 1.4 Update `PATCH /api/briefs/{id}/output-spec` to support clearing overrides
- [x] 1.5 Update snapshot creation to materialize effective `output_spec` into snapshot content
- [x] 1.6 Web API client: add create brief, create snapshot, get/patch global prefs, patch brief overrides
- [x] 1.7 Web UI: add “Create Brief”, “Create Snapshot”, “Global Preferences”, “Brief Overrides” panels
- [x] 1.8 Add backend tests for settings endpoints + snapshot resolution + clear semantics

## 2. Validation
- [x] 2.1 `openspec validate add-ui-brief-snapshot-preferences --strict`
- [x] 2.2 Backend: `ruff` + `pytest`
- [x] 2.3 Frontend: `npm run lint` + `npm run check`
