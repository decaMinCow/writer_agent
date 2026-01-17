# writer_agent2

An IDE-style app for building **novels** and **screenplays** with agentic, step-by-step workflows, versioning, and consistency checks.

## Local dev (MVP foundation)

### 1) Start Postgres (with pgvector)
From repo root:
```bash
docker compose -f infra/compose.yml up -d
```

### 2) Run the API (FastAPI)
```bash
cd apps/api
cp .env.example .env
# Optional: set OPENAI_API_KEY / OPENAI_BASE_URL in .env (env fallback),
# or configure provider settings in the web UI panel “模型提供商（OpenAI 兼容）”.
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 9761
```

Health check: `http://localhost:9761/healthz`

### 3) Run the web app (SvelteKit + Tailwind)
```bash
cd apps/web
cp .env.example .env
npm install
npm run dev -- --open
```

## OpenSpec
- Project conventions: `openspec/project.md`
- Active changes: `openspec list`

## Desktop build (Electron + offline licensing)

### One-command Windows build (PowerShell)
From repo root on Windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\build-desktop-win.ps1
```
Options:
- `-Clean` remove previous `build/` + `dist/` outputs
- `-SkipLicenseKeys` skip generating/copying the desktop public key (not recommended if licensing is enabled)
- `-NoLicense` build an unlicensed desktop app (no activation; licensing disabled by `apps/desktop/resources/desktop_config.json`)

Unlicensed shortcut:
```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\build-desktop-win-no-license.ps1 -Clean
```

### Build the web UI (static)
```bash
cd apps/web
npm install
SVELTE_ADAPTER=static PUBLIC_API_BASE_URL= npm run build
```

### Build the API binary (PyInstaller)
```bash
cd apps/api
uv sync
uv run pyinstaller --name writer-agent-api --onefile app/desktop_server.py
```
Artifacts land in `apps/api/dist/`. Electron picks up `apps/api/dist/writer-agent-api(.exe)`.

### Generate license keys (offline)
```bash
cd apps/api
uv run python -m app.tools.license_gen generate-keypair --out-dir ./license_keys
uv run python -m app.tools.license_gen issue --private-key ./license_keys/license_private_key.txt --machine-code <MACHINE_CODE>
```
Set the public key when packaging:
```bash
export WRITER_AGENT_LICENSE_PUBLIC_KEY=\"<LICENSE_PUBLIC_KEY>\"
```

### Build the desktop app
```bash
cd apps/desktop
npm install
npm run build
```

### Run desktop in dev
```bash
cd apps/web
SVELTE_ADAPTER=static PUBLIC_API_BASE_URL= npm run build
cd ../desktop
WRITER_AGENT_LICENSE_PUBLIC_KEY=\"<LICENSE_PUBLIC_KEY>\" npm run dev
```

Notes:
- Desktop uses SQLite at `app.getPath('userData')/writer_agent2.sqlite3`.
- API binds to `127.0.0.1` and serves the static UI via `STATIC_DIR`.
- Desktop env overrides:
  - `WRITER_AGENT_API_PATH`: path to packaged API binary (optional).
  - `WRITER_AGENT_STATIC_DIR`: static UI folder (optional; defaults to `apps/web/build` in dev).
  - `WRITER_AGENT_LICENSE_PUBLIC_KEY`: license public key (base64url or hex).
  - `WRITER_AGENT_LICENSE_REQUIRED`: `1` to enforce licensing (default in desktop).
  - `WRITER_AGENT_PYTHON`: Python executable when running unbundled API.
