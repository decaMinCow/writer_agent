## 1. Specification

- [x] Add/modify spec deltas for:
  - [x] `novel-to-script`: support auto-splitting a chapter into multiple script episodes
  - [x] `run-workflows`: allow selecting a novel→script split mode at run creation
  - [x] `web-ui`: expose split mode in run creation UI and update labels

## 2. Implementation (API / Workflow)

- [x] Add novel→script split mode:
  - [x] Define a small enum (e.g. `chapter_unit` / `auto_by_length`)
  - [x] Accept it on workflow run creation for `novel_to_script`
  - [x] Persist it into `workflow_runs.state`
- [x] Add chapter plan schema + prompts:
  - [x] Pydantic schema for `nts_chapter_plan` JSON output
  - [x] Add prompt templates `nts_chapter_plan_system.md` + `nts_chapter_plan_user.md`
- [x] Implement auto-by-length mode in workflow executor:
  - [x] Parse target char range from `output_spec.script_format_notes` (fallback 500–800)
  - [x] Implement `content_char_count` (remove whitespace + punctuation)
  - [x] Generate one chapter plan per chapter (STEP1 once)
  - [x] Generate N episodes per chapter (STEP2 loop), using global episode index
  - [x] Persist mapping metadata (`source_chapter_index`, `chapter_episode_sub_index`, `episode_index`)
- [x] Add length checks to critic gating:
  - [x] Hard fail if far outside range (or above soft_max)
  - [x] Allow slight overflow as a soft warning (non-blocking)

## 3. Implementation (Web UI)

- [x] Add a split mode selector when creating a `小说→剧本` run:
  - [x] Default to `按章（1章=1集）`
  - [x] Optional: `按字数自动拆集（动态）`
- [x] Ensure run list labels reflect “第X集” using script episode index when in auto-split mode (and show章索引在详情/提示中)

## 4. Validation

- [x] Backend: run `cd apps/api && uv run pytest -q`.
- [x] Frontend: run `cd apps/web && npm run check`.
- [x] Run `openspec validate add-novel-to-script-auto-split-by-length --strict`.
