## 1. UI & Behavior
- [x] Remove Brief-level output preference overrides from the right-pane UI.
- [x] Ensure UI shows only global defaults for output preferences.

## 2. Backend
- [x] Update snapshot creation to use global defaults only (ignore per-brief overrides).

## 3. Validation
- [x] Run `openspec validate remove-brief-output-overrides --strict`.
- [x] Run `cd apps/api && uv run pytest -q` and `cd apps/web && npm run check`.
