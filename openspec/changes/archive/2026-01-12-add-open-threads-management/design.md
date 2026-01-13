# Design: Open Threads (MVP)

## Data model (sketch)
- `open_threads`: `id`, `brief_snapshot_id`, `title`, `description`, `status` (open/closed), `meta`
- `open_thread_refs`: `id`, `thread_id`, `artifact_version_id`, `ref_kind` (introduced/reinforced/resolved), `quote`, `meta`

## Semantics
- Threads are scoped to a `brief_snapshot_id` (same as generation runs).
- Threads can be manually created and linked to artifact versions.
- The UI prioritizes a clean “open vs closed” view and quick navigation.

