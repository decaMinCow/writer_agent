# API

## Run locally
```bash
cp .env.example .env
# Optional: set OPENAI_API_KEY / OPENAI_BASE_URL in .env (env fallback),
# or configure provider settings in the web UI panel “模型提供商（OpenAI 兼容）”.
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 9761
```

## Run tests
Requires Postgres running (see repo `infra/compose.yml`).
```bash
cp .env.example .env
uv sync
uv run pytest
```
