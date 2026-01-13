## 1. Implementation
- [x] 1.1 Add DB migrations for open threads + references (snapshot-scoped)
- [x] 1.2 Add API endpoints: create/list/update/close threads; add/list references
- [x] 1.3 Add UI panel: thread list + detail + references jump-to-version
- [x] 1.4 Add tests: thread CRUD + reference linkage

## 2. Validation
- [x] 2.1 `openspec validate add-open-threads-management --strict`
- [x] 2.2 Backend: `uv run ruff check .` and `uv run pytest`
- [x] 2.3 Frontend: `npm run lint` and `npm run check`
