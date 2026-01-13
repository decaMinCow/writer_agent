# Design: LLM provider settings (single-user, OpenAI-compatible)

## Storage
- Use `app_settings` as the single source of truth.
- Key: `llm_provider_settings`
- Value shape (JSON):
  - `base_url` (string | null): OpenAI-compatible base URL (e.g., `https://api.openai.com/v1`)
  - `api_key` (string | null): secret (write-only via API)
  - `model` (string | null): chat model name
  - `embeddings_model` (string | null): embeddings model name
  - `timeout_s` (number | null): request timeout seconds

## API
- `GET /api/settings/llm-provider`
  - Returns safe fields + `api_key_configured` boolean.
  - MUST NOT return the API key.
- `PATCH /api/settings/llm-provider`
  - Accepts partial updates; setting `api_key: null` clears the stored key.
  - Returns the same safe shape as GET.

## Resolution rules
- For any operation that requires LLM/embeddings:
  1) Prefer DB settings when present (especially `api_key`/`base_url`).
  2) Fall back to env-based defaults (`OPENAI_API_KEY`, `OPENAI_MODEL`, etc.) to preserve existing behavior.
- LLM availability is determined by “effective api_key present”.

## Client creation
- Use the OpenAI Python SDK with explicit `base_url=` (for compatibility providers).
- Instantiate the chat and embeddings clients per request (or per workflow step) using the effective config; avoid hidden mutable process state.

## Security notes
- The key is stored server-side only (Postgres), never returned to the browser, and never logged intentionally.
- UI shows only a configured/unconfigured indicator; clearing the key is explicit.

