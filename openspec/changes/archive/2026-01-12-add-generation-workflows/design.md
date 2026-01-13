## Context
We already have:
- Versioned Briefs + immutable Brief Snapshots
- Versioned Artifacts (chapters/scenes) and Workflow Run records
- A conversational Brief Builder that updates briefs and returns a Gap Report

We now need the stepwise generation engine that turns a brief snapshot into novel/script outputs while preserving consistency and allowing edits.

## Goals / Non-Goals
Goals:
- Step-by-step generation (human-in-the-loop) with an optional “auto” mode that repeatedly executes steps.
- Every step produces persisted outputs + metadata for debugging and reproducibility.
- Consistency via CurrentState + retrieval + critic checks.

Non-Goals:
- Knowledge Graph and advanced propagation (handled later).

## Key Decision: Stepwise execution via explicit “next step” calls
Instead of a background job system for MVP, workflow execution is driven by explicit API calls:
- `POST /api/workflow-runs/{id}/next` executes exactly one step.
- The UI can:
  - call it once (“Continue”)
  - loop-call it (“Auto”)

This keeps the system simple, deterministic, and easy to debug without needing a queue/worker infra.

## State + Memory model (MVP)
- `WorkflowRun.state` stores `CurrentState` JSON and step cursor info.
- Committed artifact versions are chunked into `memory_chunks` with embeddings (pgvector).
- Retrieval returns an evidence pack (top-k chunks) used by writer/critic steps.

## Critics
- Hard checks MUST block commit and provide a machine-readable error payload.
- Soft checks provide rubric scores and targeted rewrite instructions.

## Script format configurability
Script formatting is stored in `brief.content.output_spec.script_format` and is user-editable independently.
All script generation steps MUST read and follow this setting.

## Open Questions
- Exact outline/beat schemas and thresholds can evolve, but MUST be validated at boundaries (Pydantic) and versioned.

