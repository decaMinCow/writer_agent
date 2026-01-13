## Context
We have a foundation (FastAPI + Postgres + SvelteKit) with versioned Briefs/Snapshots, versioned Artifacts, and Workflow Run records. The next step is the first “real” agent capability: converting freeform conversation into a structured Creative Brief, with continuous gap/conflict feedback.

## Goals / Non-Goals
Goals:
- Turn a user message into an updated Brief JSON object.
- Provide an explicit Gap Report (`confirmed/pending/missing/conflict`) after each message.
- Persist the conversation messages for auditability and iterative refinement.
- Keep the system controllable: structured outputs, deterministic schemas, minimal hallucination surface.

Non-Goals:
- Full long-form generation (novel/script), RAG/KG, critics, propagation engine.

## Decisions
- Use OpenAI as the default LLM provider (per product decision), configured via env vars.
- Use **structured JSON outputs** validated with Pydantic:
  - `BriefUpdate` object (partial updates to the current brief draft)
  - `GapReport` object (field-status classification + follow-up questions)
- Store brief conversation messages in a dedicated table `brief_messages` so we can:
  - replay a brief-building session
  - support “why did this field change?” debugging
- Prompts are versioned files under `apps/api/app/prompts/` so edits are diffable.

## API Shape (MVP)
- `POST /api/briefs/{brief_id}/messages`
  - Input: `{ "content": "..." }`
  - Output: `{ "brief": <BriefRead>, "gap_report": <GapReport>, "messages": [...] }` (exact schemas in implementation)

## Risks / Trade-offs
- “Confirmed vs pending” is subjective; mitigate by:
  - requiring the model to cite which user utterance supports a `confirmed` status
  - keeping `pending` as the default when uncertain
- Structured output failures; mitigate by:
  - strict JSON schema + retry with a repair prompt (bounded retries)
  - logging the raw model output for debugging (no secrets)

## Migration Plan
- Add `brief_messages` table and indexes on `(brief_id, created_at)`.

## Open Questions
- None blocking; model choice (exact OpenAI model) can be configured via env.

