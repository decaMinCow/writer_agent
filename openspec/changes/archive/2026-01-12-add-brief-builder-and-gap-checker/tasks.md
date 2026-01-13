## 1. Implementation
- [x] 1.1 Add `brief_messages` persistence (DB model + Alembic migration)
- [x] 1.2 Add OpenAI client configuration (`OPENAI_API_KEY`, model, timeouts)
- [x] 1.3 Add prompt templates for brief building + gap checking
- [x] 1.4 Implement `/api/briefs/{id}/messages` endpoint (store message → run LLM → apply patch → return gap report)
- [x] 1.5 Add bounded retry for invalid JSON outputs (repair prompt)
- [x] 1.6 Update web UI chat pane to send message + display gap report and updated brief
- [x] 1.7 Add tests: schema validation, gap report shape, happy-path endpoint smoke (LLM stub)

## 2. Validation
- [x] 2.1 `openspec validate add-brief-builder-and-gap-checker --strict`
- [x] 2.2 Backend: `ruff` + `pytest`
- [x] 2.3 Frontend: `npm run lint` + `npm run check`
