# Change: Update live execution preferences for existing runs

## Why
Today `max_fix_attempts`, `auto_step_retries`, and `auto_step_backoff_s` are read from the *snapshot-captured* `output_spec`, so changing global defaults or per-brief overrides does **not** affect already-created workflow runs. This blocks “tune retries/fix budget and keep going” during long autoruns.

## What Changes
- Treat `max_fix_attempts`, `auto_step_retries`, and `auto_step_backoff_s` as **runtime execution knobs** that can be updated and applied to **already-created workflow runs** without creating a new Snapshot.
- Keep “creative” output constraints (e.g. language, script format) **snapshot-frozen** by default to avoid mixed-format artifacts.
- Ensure both **manual step-by-step** and **server autorun** read the latest values before executing the next step (or scheduling a retry).

## Impact
- Affected specs: `execute-workflows`, `brief-snapshots`, `web-ui` (small UX copy update)
- Affected code: workflow executor (fix loop budget), autorun loop retry policy, UI helper text
