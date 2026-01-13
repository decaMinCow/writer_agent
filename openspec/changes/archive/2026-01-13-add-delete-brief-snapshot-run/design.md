# Design: Cascade Deletion + UI Hierarchy

## Overview
We implement **hard deletes** via explicit API endpoints and a backend cascade-delete service. Because database foreign keys do not use `ON DELETE CASCADE`, the backend must delete in a safe order that respects constraints.

## Data ownership model
- **Brief** owns:
  - `brief_snapshots`
  - `brief_messages`
- **Brief Snapshot** owns snapshot-scoped data:
  - `workflow_runs` (and their `workflow_step_runs`)
  - `artifact_versions` linked to the snapshot (user/agent)
  - derived/index data: `memory_chunks`, `kg_*`, `lint_issues`, `propagation_*`, `open_threads*`, `snapshot_glossary_entries`
- **Workflow Run** owns:
  - `workflow_step_runs`
  - `artifact_versions` produced by that run (and any rows that reference those versions)

## Cascade strategy
Implement a small service (e.g. `app/services/cascade_delete.py`) that provides:
- `delete_workflow_run(run_id)`
- `delete_brief_snapshot(snapshot_id)`
- `delete_brief(brief_id)`

### Deletion order (core)
To satisfy FK constraints, delete in this order (subset depending on target):
1. `open_thread_refs` (by `thread_id` or `artifact_version_id`)
2. `artifact_impacts`
3. `propagation_events`
4. `lint_issues`
5. `kg_relations`
6. `kg_events`
7. `kg_entities`
8. `snapshot_glossary_entries`
9. `memory_chunks`
10. `workflow_step_runs`
11. `artifact_versions`
12. `workflow_runs`
13. `brief_messages`
14. `brief_snapshots`
15. `briefs`
16. Cleanup: delete `artifacts` that have no remaining `artifact_versions`

## UI hierarchy
The current UI loads all workflow runs and shows them as a flat list. We will:
- Filter runs by `selectedSnapshot.id` when a snapshot is selected.
- Keep the navigation hierarchy visible:
  - Selecting a run should not clear the selected brief/snapshot context.

## Run display naming (Chinese)
Compute a display label from:
- `run.kind`: novel / script / novel_to_script
- `run.state.cursor.phase` and index keys (`chapter_index`, `scene_index`)

Example mapping (minimal, extendable):
- 小说：
  - `novel_outline` → `小说 · 大纲`
  - `novel_beats` → `小说 · 分章`
  - `novel_chapter_draft` → `小说 · 第N章 · 草稿`
  - `novel_chapter_critic` → `小说 · 第N章 · 审校`
  - `novel_chapter_fix` → `小说 · 第N章 · 修复`
  - `novel_chapter_commit` → `小说 · 第N章 · 提交`
  - `done` → `小说 · 完成`
- 剧本：同理，按 scene phases
- 小说→剧本：按 nts phases

