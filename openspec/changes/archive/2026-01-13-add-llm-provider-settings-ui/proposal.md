# Change: Add model provider settings UI (OpenAI-compatible)

## Why
The app needs a built-in way to configure an OpenAI-compatible provider because the base URL and credentials may change frequently. Editing `.env` and restarting the API is slow and error-prone.

## What Changes
- Add a single-user **LLM provider settings** record persisted in Postgres (via `app_settings`).
- Add API endpoints to **get/patch** provider settings:
  - Safe fields (e.g., `base_url`, model names, timeout) are readable.
  - The API key is write-only: responses only return `api_key_configured: true|false`.
- Update LLM-backed endpoints/workflows to **resolve provider config from DB** (env stays as fallback).
- Add a web UI panel to edit provider settings (base URL, models, timeout, API key) and to clear the key.

## Impact
- Affected specs: `web-ui` (modified), `llm-provider-settings` (new)
- Affected backend: settings store + routing; LLM resolution in LLM-dependent routes/workflows.
- Affected frontend: API client functions and a new panel in the IDE UI.

## Non-goals (for this change)
- Multiple provider profiles / one-click profile switching.
- Supporting non-OpenAI protocols (Anthropic native, etc.).
- Key encryption-at-rest (defer; single-user MVP stores key in DB, never returns it).

