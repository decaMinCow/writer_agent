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
