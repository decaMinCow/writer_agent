## 1. Desktop packaging (Electron)
- [x] Create `apps/desktop` Electron app skeleton (dev run + build).
- [x] Implement sidecar lifecycle: pick port → spawn API → wait healthz → open window → stop on quit.
- [x] Add build scripts for macOS/Windows installers (electron-builder) and document them.

## 2. Embedded database (SQLite)
- [x] Add SQLite runtime support (`sqlite+aiosqlite`) and store DB file under a user data directory.
- [x] Make SQLAlchemy models compatible with both Postgres (dev) and SQLite (desktop) where required.
- [x] Implement RAG retrieval fallback for SQLite (Python similarity) while keeping Postgres behavior acceptable.
- [x] Add automatic DB initialization / migration on API startup for desktop mode.
- [x] Add tests for SQLite mode initialization and basic CRUD (brief/snapshot/artifacts).

## 3. Offline licensing (machine-bound)
- [x] Add backend license store + endpoints: machine-code, status, activate, clear.
- [x] Add license enforcement middleware (403 gate for `/api/*` except license endpoints).
- [x] Add a local CLI tool to generate license codes from a machine code (private key stays outside repo).
- [x] Add UI panel for activation (machine code + paste license + status).
- [x] Add tests for license verification + enforcement behavior.

## 4. Docs / Validation
- [x] Update `README.md` with desktop build/run instructions and troubleshooting.
- [x] Run `openspec validate <change-id> --strict`.
- [x] Run `cd apps/api && uv run pytest -q` and `cd apps/web && npm run check`.
