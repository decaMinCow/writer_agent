## 1. Implementation
- [x] 1.1 Add API client method to create artifact versions from the web UI
- [x] 1.2 Add UI: select an artifact version and show full content
- [x] 1.3 Add UI editor: edit text and save as `source=user` (copy `brief_snapshot_id` from base)
- [x] 1.4 Backend: on `POST /api/artifacts/{id}/versions`, index into memory when `brief_snapshot_id` present and embeddings configured (best-effort)
- [x] 1.5 Add/adjust backend tests for create-version indexing behavior

## 2. Validation
- [x] 2.1 Run backend: `uv run ruff check .` and `uv run pytest`
- [x] 2.2 Run frontend: `npm run lint` and `npm run check`
