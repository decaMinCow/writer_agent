## 1. Implementation
- [x] 1.1 Add export endpoints: novel markdown/text; script fountain (snapshot-scoped)
- [x] 1.2 Add glossary storage (snapshot-scoped) + apply-at-export implementation
- [x] 1.3 Add UI: export buttons + glossary editor (minimal)
- [x] 1.4 Add tests: export ordering + fountain formatting smoke tests

## 2. Validation
- [x] 2.1 `openspec validate add-export-and-formatting-tools --strict`
- [x] 2.2 Backend: `uv run ruff check .` and `uv run pytest`
- [x] 2.3 Frontend: `npm run lint` and `npm run check`
