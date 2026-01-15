## 1. Implementation

- [x] Add episode-based phases for `novel_to_script` execution:
  - [x] Default new runs to `nts_episode_breakdown` (while keeping `nts_scene_*` compatibility for existing runs).
  - [x] Use `cursor.chapter_index` as episode index (1章=1集).
- [x] Implement `nts_episode_breakdown` (STEP1):
  - [x] Input: the current novel chapter text + digests, plus `CurrentState`.
  - [x] Output: structured breakdown JSON (events/conflicts/emotional beats) stored in `run.state`.
- [x] Implement `nts_episode_draft` (STEP2):
  - [x] Generate one complete episode script with multiple scenes.
  - [x] Enforce header/numbering style: `第X集` once; scene blocks `X.Y`.
  - [x] Provide continuity context: prior committed episode fact/tone digests + `CurrentState`.
- [x] Implement episode critic/fix/commit loop:
  - [x] Add hard format checks for episode output (header/scene numbering/prompt leakage).
  - [x] Reuse existing critic + rewrite loop for targeted fixes when needed.
  - [x] Commit one script artifact version per episode (ordinal = chapter_index), update `CurrentState`, and reset per-episode fix counters.
- [x] Update Web UI run labels for episode phases:
  - [x] Show `小说→剧本 · 第X集 · 拆解/草稿/审校/修复/提交`.
  - [x] Add Chinese descriptions for new hard error codes.

## 2. Validation

- [x] Add backend tests for episode-based novel→script:
  - [x] New run defaults to episode phase.
  - [x] Episode format guard rejects invalid header/scene numbering.
  - [x] Happy-path commit produces one script artifact version per chapter.
- [x] Run `cd apps/api && uv run pytest`.
- [x] Run `cd apps/web && npm run check`.
- [x] Run `openspec validate update-novel-to-script-episode-workflow --strict`.
