## 1. Implementation
- [x] Add a server-side resolver for runtime execution preferences (merge global defaults + per-brief overrides).
- [x] Use resolved `max_fix_attempts` in `execute_next_step` fix loop gating (all workflows).
- [x] Use resolved `auto_step_retries` / `auto_step_backoff_s` in autorun loop retry scheduling.
- [x] Add/adjust tests to prove updated preferences affect already-created runs.

## 2. UI / UX
- [x] Update UI helper text to clarify that these three knobs affect existing runs starting from the next step.

## 3. Validation
- [x] Run `openspec validate update-live-execution-preferences --strict`.
- [x] Run `cd apps/api && uv run pytest -q`.
