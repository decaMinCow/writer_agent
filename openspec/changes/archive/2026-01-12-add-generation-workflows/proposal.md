# Change: Add novel/script generation workflows (stepwise)

## Why
After Brief Builder, the core product value is generating novels and scripts via a **step-by-step workflow** that is resumable, debuggable, and consistent with the versioned Brief Snapshot.

## What Changes
- Add a **stepwise workflow execution model**:
  - Each workflow run has ordered steps (outline → beats → draft → critique → fix → commit)
  - The UI can run “Continue” to execute the next step, or run “Auto” to iterate until completion
- Add **Novel generation**:
  - Outline and chapter generation with commit artifacts + dual digests (fact/tone)
  - Update `CurrentState` after each commit
- Add **Script generation**:
  - Scene list and scene drafting in screenplay format
  - Script formatting MUST follow `brief.output_spec.script_format`
- Add **Memory/RAG MVP** using pgvector:
  - Index committed artifacts and retrieve relevant evidence for each step
- Add **Critic + Fix loop MVP**:
  - Hard checks (continuity/state/world rules) gate commits
  - Soft checks (style/pacing/OOC) provide rubric scores and targeted rewrites

## Impact
- Affected specs (new): `execute-workflows`, `novel-generation`, `script-generation`, `memory-rag`, `state-updates`, `critic-rubric`
- Affected code: `apps/api/**` (workflow execution endpoints, RAG storage, LLM prompting), `apps/web/**` (step runner UI)
- Data model: adds memory chunk storage (pgvector) and state/digest fields

## Non-Goals (for this change)
- Knowledge Graph (Neo4j) integration (can be a later enhancement)
- Novel → Script conversion and propagation engine (separate change)

