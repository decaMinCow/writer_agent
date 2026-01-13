# Change: Add novel → script workflow (stepwise)

## Why
Novel → Script conversion is a key product differentiator: it lets users reuse a generated (or edited) novel as “evidence” to produce a screenplay without drifting from established plot facts.

## What Changes
- Implement `WorkflowKind.novel_to_script` as a stepwise workflow run (pause/resume, one-step execution).
- Source selection (MVP):
  - Use the **latest committed novel chapter versions** for the same `brief_snapshot_id`.
  - If no novel chapters exist for the snapshot, fail with a user-actionable error.
- Pipeline steps (MVP):
  - Collect source chapter digests (and/or evidence) → generate `scene_list`
  - For each scene: draft → critic (fidelity + shootability + format) → fix loop → commit
- Script formatting MUST honor `brief_snapshot.content.output_spec.script_format`.
- Web UI: allow creating and running `novel_to_script` runs (remove “未实现” block).

## Impact
- Backend: `apps/api/app/services/workflow_executor.py` adds a new state machine branch.
- Prompts: add novel→script specific prompt templates.
- Tests: add workflow tests for source selection, step transitions, and fidelity gating.
- UI: enable `novel_to_script` run creation and show step outputs like other workflows.

## Non-Goals (for this change)
- Full change propagation engine (facts extraction + impact graph).
- Rich UI scene/chapter mapping editor (manual reorder/split/merge in UI).
- Deterministic (non-LLM) fidelity linter beyond existing hard/soft gating.

