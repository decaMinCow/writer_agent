# Project Context

## Purpose
Build a “creative IDE” for long-form storytelling that uses AI agents to generate and iterate on **novels** and **screenplays** with strong consistency guarantees.

Core product outcomes:
- Turn a conversational intake into a **versioned Creative Brief** (constraints + assets + output specs).
- Run **step-by-step workflows** (brief → outline → beats → draft → critique → fix → commit) with **human-in-the-loop** editing or full automation.
- Support **novel-only**, **script-only**, or **novel → script** pipelines while preserving story facts and intent.
- Maintain consistency via **structured state**, **retrieval (RAG)**, **hard/soft checks**, and **change propagation** (like refactors in code).

## Tech Stack
MVP-recommended stack (adjust as needed; keep this file updated when decisions change):
- **Orchestration**: LangGraph (stateful, interruptible, resumable agent graphs)
- **LLM providers**: provider-agnostic (OpenAI/Anthropic/etc), configured via env vars (no keys in repo)
- **Backend API**: FastAPI (Python)
  - **Schemas**: Pydantic v2 (validate all LLM/IO boundaries)
  - **DB access**: SQLAlchemy 2.x + Alembic migrations (or SQLModel if preferred)
  - **Async**: asyncio + `asyncpg` for Postgres
  - **OpenAPI**: FastAPI-generated API docs as contract
- **Primary DB**: Postgres (source of truth for briefs, versions, artifacts, events)
- **Vector search**: pgvector (Postgres extension) for MVP → Milvus/Pinecone optional at scale
- **Graph (optional)**: Neo4j (or Postgres adjacency tables) for Knowledge Graph queries
- **Object storage**: S3-compatible (exports, large artifacts, attachments)
- **Frontend**: SvelteKit (TypeScript) “IDE” UI (chat + workflow + asset panel)
  - **Styling**: Tailwind CSS
  - **Client state**: Svelte stores for brief/workflow/asset panel state
  - **Streaming**: SSE/WebSocket for token streaming + step updates (as supported by backend)

## Project Conventions

### Code Style
General:
- Prefer **typed schemas** for all persisted or LLM-produced data (e.g., Pydantic/Zod); validate at boundaries.
- Keep prompts as **versioned templates** (files), not inline strings; changes should be reviewable/diffable.
- Use explicit names over abbreviations (`chapter_digest`, not `cd`).

Python (FastAPI/LangGraph):
- Format/lint with `ruff` (and `ruff format` if enabled); keep imports sorted.
- Prefer explicit response/request models (Pydantic) over ad-hoc dicts.
- Keep side effects behind service boundaries (DB writes, vector upserts, S3 uploads).

SvelteKit (TypeScript) + Tailwind:
- Use `prettier` (with Tailwind plugin if configured) for consistent class ordering.
- Keep UI state in stores; avoid business logic in components (push to services/lib).
- Use file-based routing conventions; keep components small and composable.

LLM interaction:
- Prefer **structured output** (JSON schema) for planning, state diffs, and checks.
- Every generation step should emit: `artifact` + `metadata` (inputs, brief snapshot id, evidence ids, state diff).

Naming:
- Domain objects use consistent casing across code and DB (pick one and stick to it).
- Avoid ambiguous terms; use the glossary in “Domain Context”.

### Architecture Patterns
Treat stories like compilable projects:
- **Brief → State → Evidence → Output**: generation is always constrained by the current brief snapshot, current state, and retrieved evidence.
- **State machine orchestration**: each workflow step is a node that can be paused, edited, rerun, or resumed.
- **Event sourcing / versioning**: store snapshots + diffs for Brief, Chapters/Scenes, State/KG updates, and user edits.
- **Critique + fix loop**: run hard checks (must-fix) and soft checks (quality) and rewrite only failing spans to prevent drift.
- **Change propagation**: manual edits trigger extraction of “fact changes” and update Brief/State/KG plus mark impacted artifacts for repair.

Agent modules (replaceable by implementation):
- `BriefBuilder` (conversation → brief draft)
- `GapChecker` (missing/pending/conflict detection + follow-up questions)
- `PlannerNovel`, `PlannerScript` (outline/scene list planning)
- `Retriever` (RAG + KG + State → evidence pack)
- `WriterNovel`, `WriterScript` (drafting)
- `CriticLogic`, `CriticStyle` (hard/soft checks + rubric)
- `MemoryWriter` (digests + vector upserts + state/kg commit)
- `PropagationEngine` (edit diffs → updates + impact analysis)

### Testing Strategy
Minimum bar (especially for consistency):
- Unit tests for **hard checks** (timeline, presence, inventory, world rules) and propagation/impact logic.
- Golden/snapshot tests for **schemas** and prompt templates (prevent accidental drift).
- Integration tests for end-to-end workflows using a **stubbed LLM** and deterministic fixtures.
- Property/invariant tests for State updates (e.g., “dead character cannot reappear”).

Recommended tools:
- Backend: `pytest` + `pytest-asyncio`, `httpx` for API tests, and DB fixtures for Postgres.
- Frontend: `vitest` for unit tests; `playwright` for basic workflow E2E (optional for MVP).

### Git Workflow
- Use short-lived feature branches and PRs; keep PRs scoped to one change intent.
- Prefer **Conventional Commits** (`feat:`, `fix:`, `docs:`, `refactor:`) unless the repo adopts a different standard.
- For product-level changes (new capabilities, breaking changes, architecture shifts), use OpenSpec `openspec/changes/<change-id>/` and validate with `openspec validate --strict` before implementation.

## Domain Context
Key artifacts (source of truth is the DB; “commit” means persisted + versioned):
- **Brief**: the work’s configuration and constraints (title/logline/theme/style/world/characters/structure/output specs/prompt rules).
- **Brief Snapshot**: immutable version of the Brief used for a generation run.
- **Outline / Beat Sheet**: structured plan for chapters/scenes (goals, beats, twists, hooks).
- **Novel Chapter**: prose output, plus chapter metadata and two digests:
  - `FactDigest` (what objectively happened)
  - `ToneDigest` (voice, pacing, mood)
- **Script Scene**: screenplay-format scene with title (INT/EXT), time, location, action, dialogue.
- **CurrentState**: structured truth for time/place/presence/inventory/relationships/known facts.
- **KnowledgeGraph (KG)**: entities/relations/events (optional but recommended as projects scale).
- **Open Threads**: unresolved mysteries/foreshadowing items that must be tracked and closed.

Workflows:
- **Novel**: Brief → Outline → Chapter beats → (retrieve → write → critique → fix → commit) × N → unify polish.
- **Script**: Brief → Scene list → Scene beats → (write → critique → fix → commit) × N.
- **Novel → Script**: extract scenes + key dialogue from novel text → map to scene list → write script → fidelity check → polish.

Quality model:
- **Hard checks** (must pass): continuity, presence, inventory, timeline, world rules.
- **Soft checks** (rated): OOC detection, POV drift, style fingerprint drift, pacing, dialogue distinctiveness, “shootability” for scripts.

## Important Constraints
- User-configured **rating boundaries** and forbidden content MUST be enforced throughout the pipeline.
- “Reference works” are for **style alignment only**; avoid plot/character copying.
- Keep long-form runs reliable: every step must be resumable, debuggable, and versioned; no hidden state.
- Do not store secrets in prompts/logs; keep PII exposure minimal and configurable.

## External Dependencies
- LLM + embeddings provider(s) (keys via env vars; support provider swapping).
- Postgres + pgvector.
- S3-compatible object storage for exports/attachments.
- Optional: Neo4j (KG), Milvus/Pinecone (vector at scale).
