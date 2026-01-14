## 1. Implementation

- [x] Extend global output defaults to include `auto_step_retries` and `auto_step_backoff_s` (API + persistence).
- [x] Extend per-brief output overrides to support `auto_step_retries` and `auto_step_backoff_s`.
- [x] Implement autorun loop auto-retry on retryable step failures (with backoff + attempt tracking in `run.state`).
- [x] Emit SSE `log` events for retry scheduling and retry exhaustion.
- [x] Update web UI settings panel to edit the new global defaults and per-brief overrides, and show effective values.

## 2. Validation

- [x] Add backend tests: autorun retries a transient step failure and eventually succeeds.
- [x] Add backend tests: autorun stops after retry limit is exceeded and reports exhaustion clearly.
- [x] Run `cd apps/api && uv run pytest`.
- [x] Run `cd apps/web && npm run check`.
