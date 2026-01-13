# Design: Novel → Script workflow (MVP)

## Overview
Add a `novel_to_script` workflow that converts previously committed novel chapters into committed script scenes, step-by-step.

The workflow uses:
- **Brief Snapshot** as immutable configuration (including effective `output_spec`)
- **Committed novel chapters** as source-of-truth evidence
- **RAG retrieval** (pgvector memory chunks) to inject relevant passages into each step
- **Critic + fix loop** to gate commits and avoid drift

## Source Selection (MVP)
- Identify source novel text by querying artifact versions where:
  - `brief_snapshot_id == run.brief_snapshot_id`
  - `artifact.kind == novel_chapter`
  - pick the latest version per chapter ordinal
- Extract `fact_digest`/`tone_digest` from `artifact_versions.metadata` when present.
- If zero source chapters exist, fail the run with `detail=novel_source_missing`.

## Phases
Suggested cursor phases:
1. `nts_scene_list`:
   - Input: brief snapshot JSON + chapter digests (ordered)
   - Output: `scene_list` (structured JSON)
2. Loop `scene_index`:
   - `nts_scene_draft`: draft screenplay scene (format per `output_spec`)
   - `nts_scene_critic`: evaluate fidelity to evidence + shootability/clarity; produce `state_patch`, rubric, rewrite instructions
   - `nts_scene_fix`: targeted rewrite by paragraph indices
   - `nts_scene_commit`: persist `ArtifactKind.script_scene` version + digests + index into memory store

## Prompts
Add dedicated templates for:
- Scene list extraction using chapter digests (not full text)
- Scene drafting that prioritizes preserving factual beats/dialogue from evidence
- Critic tuned for fidelity: “MUST NOT introduce events that contradict evidence”

Reuse existing rewrite templates (paragraph replacement) for fix loop.

## Output Spec
- `brief_snapshot.content.output_spec` is treated as resolved effective defaults+overrides.
- The workflow passes output spec into scene inputs and/or system prompt so writers follow the format.

## Error Handling
- No novel source: fail run with actionable message and `missing_sources` metadata.
- Critic hard fail: block commit; attempt fix up to N times; if still failing, fail run.

## UI
- Enable creating `novel_to_script` runs from selected snapshots.
- Keep current step runner controls; display scene list and committed scene references.

