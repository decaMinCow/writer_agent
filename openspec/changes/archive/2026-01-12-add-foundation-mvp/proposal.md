# Change: Add MVP project foundation

## Why
We need a working, end-to-end baseline (API + UI + database + workflow run records) so the “novel + script AI Agent IDE” can be implemented incrementally with versioning, resumability, and consistency controls.

## What Changes
- Introduce a local development setup (docker-compose) for Postgres + pgvector.
- Scaffold a FastAPI backend with typed schemas, database migrations, and core persistence primitives:
  - Creative Briefs + Brief Snapshots (versioned)
  - Artifacts (novel chapters / script scenes) with version history
  - Workflow Runs and Step Runs (pause/resume, auditability)
- Scaffold a SvelteKit + Tailwind IDE UI with the 3-pane layout:
  - Chat pane (placeholder in this change)
  - Step/workflow pane (runs + step status)
  - Story assets pane (brief/snapshots/artifacts browser)
- Establish baseline conventions (structure, scripts) for future capability work (brief builder, generation loops, RAG, critics, propagation).

## Impact
- Affected specs (new): `run-local-dev`, `manage-briefs`, `manage-artifacts`, `run-workflows`, `render-ide-ui`
- Affected code (new): `apps/api/**`, `apps/web/**`, `infra/**` (created in implementation phase)
- Data model: adds initial Postgres schema for briefs/artifacts/workflows

## Non-Goals (for this change)
- Implementing LLM generation, RAG, Knowledge Graph, critics, or propagation logic (covered by later changes)
- Authentication / multi-user support (explicitly single-user, no login for MVP)

