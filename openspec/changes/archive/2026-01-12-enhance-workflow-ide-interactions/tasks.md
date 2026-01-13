## 1. Implementation
- [x] 1.1 Add API: fork workflow run from selected run/step (copy state)
- [x] 1.2 Add API: targeted rewrite for an artifact version (creates new version with provenance)
- [x] 1.3 Add UI: fork button + run state viewer/editor (minimal)
- [x] 1.4 Add UI: select text / provide instruction → targeted rewrite → new version shown
- [x] 1.5 Add tests: fork copies state; rewrite creates version and indexes memory when snapshot present

## 2. Validation
- [x] 2.1 `openspec validate enhance-workflow-ide-interactions --strict`
- [x] 2.2 Backend: `uv run ruff check .` and `uv run pytest`
- [x] 2.3 Frontend: `npm run lint` and `npm run check`
