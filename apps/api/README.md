# API

## Run locally
```bash
cp .env.example .env
# set OPENAI_API_KEY in .env to enable brief chat updates
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

## Run tests
Requires Postgres running (see repo `infra/compose.yml`).
```bash
cp .env.example .env
uv sync
uv run pytest
```
