# Change: Add artifact editing + memory indexing for user edits

## Why
Today, artifact versions created by workflows are indexed into memory (RAG), but **user edits** created as new artifact versions are not. This means retrieval can continue to pull outdated text even after a user corrects or rewrites content.

We also lack a first-class UI flow to edit an artifact version and save it as a new immutable, user-authored version.

## What Changes
- Add an IDE UI editor to:
  - Open an artifact version
  - Edit its text
  - Save as a **new** artifact version (`source=user`)
- Extend artifact version creation to **optionally index** the new version into `memory_chunks`:
  - Only when `brief_snapshot_id` is present
  - Only when embeddings are configured
  - Best-effort: do not block saving the version on indexing failures

## Impact
- Affected specs: `manage-artifacts` (UI editing), `memory-rag` (index on create)
- Affected code:
  - Backend: `apps/api/app/api/routers/artifacts.py`, `apps/api/app/services/memory_store.py`
  - Frontend: `apps/web/src/routes/+page.svelte`, `apps/web/src/lib/api.ts`
- Data model: no schema change (reuse `artifact_versions`, `memory_chunks`)

## Non-Goals (for this change)
- Diff/merge tooling, tracked edits, or multi-user collaboration
- Automatic propagation/refactor of downstream artifacts when text is edited
- Background job queue for embeddings (indexing is synchronous MVP)

