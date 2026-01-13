## 1. Implementation
- [x] 1.1 Add DB migrations for KG and lint issue tables (snapshot-scoped)
- [x] 1.2 Implement KG store service (Postgres) + basic query endpoints
- [x] 1.3 Implement linter service (hard/soft issues) + API endpoints
- [x] 1.4 Add minimal UI panels for KG browsing and lint issues (link to artifact versions)
- [x] 1.5 Add tests: CRUD/query for KG tables; linter rule unit tests

## 2. Validation
- [x] 2.1 `openspec validate add-knowledge-graph-and-story-linter --strict`
- [x] 2.2 Backend: `uv run ruff check .` and `uv run pytest`
- [x] 2.3 Frontend: `npm run lint` and `npm run check`
