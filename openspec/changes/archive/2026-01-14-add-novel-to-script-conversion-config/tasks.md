## 1. Implementation

- [x] Extend `POST /api/workflow-runs` to accept `source_brief_snapshot_id` and `conversion_output_spec` for `novel_to_script`.
- [x] Persist those inputs into `workflow_runs.state` (JSON-safe) and validate source snapshot belongs to the same Brief.
- [x] Update `novel_to_script` execution to:
  - [x] load novel sources + evidence from `state.novel_source_snapshot_id` (fallback to run snapshot)
  - [x] merge `state.conversion_output_spec` into `brief_snapshot.content.output_spec` for prompts
- [x] Update web UI “从 Snapshot 创建 Run” to expose:
  - [x] source snapshot selector (default current snapshot)
  - [x] conversion script format + notes inputs (stored in run via API)

## 2. Validation

- [x] Add backend test: `novel_to_script` can use a different source snapshot and does not fail with `novel_source_missing`.
- [x] Add backend test: `conversion_output_spec` is reflected in the draft prompt (e.g., custom + notes).
- [x] Add backend test: reject source snapshot not in the same brief.
- [x] Run `cd apps/api && uv run pytest`.
- [x] Run `cd apps/web && npm run check`.
- [x] Run `openspec validate add-novel-to-script-conversion-config --strict`.
