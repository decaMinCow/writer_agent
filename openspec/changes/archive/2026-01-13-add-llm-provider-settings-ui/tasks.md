## 1. Implementation
- [x] Add provider settings schemas and DB store utilities (`app_settings` key `llm_provider_settings`).
- [x] Add `/api/settings/llm-provider` GET/PATCH endpoints (API key write-only; return `api_key_configured`).
- [x] Implement effective-provider resolution and wire it into LLM-dependent routes/workflow execution paths.
- [x] Add a web UI panel + client API bindings to view/update provider settings and clear key.
- [x] Update docs (`apps/api/.env.example`, `README.md`) to mention provider settings and `OPENAI_BASE_URL` fallback.

## 2. Validation
- [x] `openspec validate add-llm-provider-settings-ui --strict`
- [x] `cd apps/api && uv run pytest`
- [x] `cd apps/web && npm run lint && npm run check`
