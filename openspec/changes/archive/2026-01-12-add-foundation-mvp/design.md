## Context
This repo currently contains only OpenSpec scaffolding. The product we’re building is a “creative IDE” for long-form storytelling (novels + screenplays) with strong consistency and editability guarantees.

Constraints confirmed by user:
- Single-user, no login
- Local development via `docker-compose` is acceptable
- Default LLM provider: OpenAI
- Primary language: Simplified Chinese
- Script formatting preferences must be configurable (not hard-coded)

## Goals / Non-Goals
Goals:
- Establish the minimum foundation to support later capabilities without rework:
  - Versioned Briefs and Brief Snapshots
  - Versioned Artifacts (chapters/scenes) tied to runs/snapshots
  - Workflow run records (status, steps, audit trail)
  - UI shell that can display/edit these entities

Non-Goals:
- LLM prompting, streaming generation, RAG/KG, critics, propagation engine (later changes)

## Decisions
- **Backend**: FastAPI (Python) with Pydantic v2 schemas at boundaries.
- **Persistence**: Postgres as system of record; use JSONB for flexible, evolvable domain payloads (Brief, State, metadata) while also storing key indexed columns (ids, timestamps, types, ordering).
- **Migrations**: Alembic for schema evolution.
- **Vector search**: pgvector enabled in Postgres from day 1 (even if unused in this change) to avoid infra churn later.
- **Frontend**: SvelteKit (TypeScript) + Tailwind CSS, structured as a 3-pane IDE layout.
- **Script format preference**: stored as part of the Brief `output_spec` and editable independently (UI “Output Settings” section). Later script generation MUST read from this value.

## Data Model (MVP shape)
This change establishes the *storage primitives*; later changes add richer schemas.

- `briefs`: mutable draft brief (JSONB payload + metadata)
- `brief_snapshots`: immutable snapshots of a brief used for a specific run/version
- `artifacts`: logical artifact identity (e.g., “Chapter 07”)
- `artifact_versions`: immutable versions of an artifact (full text + metadata) created by user or agent
- `workflow_runs`: a run instance (novel/script/convert), referencing a brief snapshot
- `workflow_step_runs`: per-step status and outputs (artifact references + metadata)

## Risks / Trade-offs
- Using JSONB accelerates iteration but can hide schema drift; mitigate by:
  - validating LLM outputs with Pydantic models (even if stored as JSONB)
  - keeping “shape contracts” in OpenSpec requirements and tests

## Migration Plan
- Add initial Alembic migration for core tables.
- Provide `docker-compose` service for Postgres with pgvector enabled.

## Open Questions
- None for foundation; later changes will decide the exact Brief schema, critics rubrics, and propagation semantics.

