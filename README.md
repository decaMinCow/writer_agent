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
# set OPENAI_API_KEY in .env to enable the Brief Builder endpoints
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Health check: `http://localhost:8000/healthz`

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
