## 1. Implementation
- [x] 1.1 Create repo layout: `apps/api`, `apps/web`, `infra`
- [x] 1.2 Add `infra/compose.yml` for Postgres + pgvector (dev-only)
- [x] 1.3 Scaffold FastAPI app with config, health endpoint, OpenAPI
- [x] 1.4 Add Postgres connection layer + Alembic migrations baseline
- [x] 1.5 Implement persistence + API for Briefs and Brief Snapshots
- [x] 1.6 Implement persistence + API for Artifacts and Artifact Versions
- [x] 1.7 Implement persistence + API for Workflow Runs and Step Runs
- [x] 1.8 Scaffold SvelteKit + Tailwind app with 3-pane IDE layout
- [x] 1.9 Wire UI to list/view briefs, snapshots, runs, artifacts (read-only MVP)
- [x] 1.10 Add minimal tests (backend unit + API smoke) and lint/format scripts

## 2. Validation
- [x] 2.1 Run backend checks: lint/format + `pytest`
- [x] 2.2 Run frontend checks: `pnpm lint` + `pnpm check` (or equivalent)
- [x] 2.3 Confirm local dev: Postgres up via docker-compose; API + UI start cleanly
