## 1. Implementation
- [x] 1.1 Add DB migrations: propagation events + impacted artifacts markers
- [x] 1.2 Add change extractor endpoint (base vs edited) returning patches + impact report
- [x] 1.3 Add apply endpoint to persist propagation event and mark impacted artifacts
- [x] 1.4 Add “repair” endpoint that creates new artifact versions for selected impacted items
- [x] 1.5 Add UI: show change summary + impacted list + one-click repair
- [x] 1.6 Add tests: patch persistence + impact marking + repair creates new versions

## 2. Validation
- [x] 2.1 `openspec validate add-propagation-engine --strict`
- [x] 2.2 Backend: `uv run ruff check .` and `uv run pytest`
- [x] 2.3 Frontend: `npm run lint` and `npm run check`
