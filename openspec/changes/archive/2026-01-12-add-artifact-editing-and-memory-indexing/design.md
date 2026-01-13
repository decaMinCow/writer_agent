# Design: Artifact editing + memory indexing

## Goals
- Let the user edit artifact content inside the IDE and save edits as a new immutable `artifact_versions` row.
- Ensure RAG evidence reflects the latest edits by indexing new user versions into `memory_chunks` when scoped to a `brief_snapshot_id`.

## UX / Version Semantics
- Editing is “copy-on-write”:
  - The user selects an existing artifact version as a base.
  - The system saves the edited text as a **new** version with `source=user`.
  - Prior versions are retained for audit and rollback.
- The UI keeps editing minimal:
  - Select version → edit text → save → refresh version list.

## Memory Indexing Semantics
- Indexing is triggered on **artifact version creation** (API).
- Indexing only runs when:
  - `brief_snapshot_id` is provided, and
  - an embeddings client is configured.
- Indexing is best-effort:
  - Failures to embed/index MUST NOT prevent the artifact version from being saved.
  - The API response still returns the created artifact version.

## Provenance Metadata (MVP)
- When saving a user edit, the UI SHOULD include metadata:
  - `edited_from_version_id`: the base version id
  - `edited_at`: ISO timestamp

