# Change: Add knowledge graph + story linter (Postgres-backed)

## Why
Consistency is the core product promise. We need a “compiler/linter” layer that can validate story facts (timeline, presence, inventory, world rules) and a knowledge representation to support inspection and debugging.

The user prefers not to introduce Neo4j for MVP; we will implement a Postgres-backed graph and keep the storage interface swappable.

## What Changes
- Backend:
  - Add Postgres tables for a snapshot-scoped Knowledge Graph (entities/relations/events).
  - Add a linter that produces **hard** and **soft** issues with references to artifact versions.
  - Add API endpoints to query KG + lint results.
- Frontend:
  - Add a minimal “KG / Lint” panel to view issues and navigate to affected artifacts/versions.

## Impact
- Affected specs (new): `knowledge-graph`, `story-linter`
- Affected specs (update): `web-ui`
- Affected code:
  - Backend: new models + migrations + services + routers
  - Frontend: new panels in IDE UI

## Non-Goals (for this change)
- Neo4j integration, advanced graph visualization, or complex multi-hop analytics UI
- Perfect automatic extraction (MVP uses best-effort extraction and user correction later)

