# Design: Workflow IDE interactions (MVP)

## Forking semantics
- Fork creates a new `workflow_runs` row with:
  - same `kind` and `brief_snapshot_id`
  - copied `state` (optionally with cursor override)
- Fork does not mutate the original run.

## Targeted rewrite semantics
- A rewrite creates a new `artifact_versions` row:
  - references the base version via metadata
  - preserves `brief_snapshot_id` for RAG

## Editing intermediate artifacts
- MVP allows editing a step output (JSON/text) and saving it as run state override for the next step.

