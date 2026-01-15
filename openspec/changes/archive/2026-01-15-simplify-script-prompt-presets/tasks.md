## 1. Specification

- [x] Add/modify spec deltas for:
  - [x] `global-settings`: global prompt preset catalog (script + novel_to_script)
  - [x] `run-workflows`: allow choosing a prompt preset at run creation
  - [x] `novel-to-script`: ignore snapshot/brief notes; use preset text for conversion notes
  - [x] `script-generation`: use preset text as script style notes
  - [x] `web-ui`: manage presets + select preset when creating runs

## 2. Implementation (API)

- [x] Add prompt preset schemas (read/patch) for settings.
- [x] Persist prompt presets in `AppSetting` (single-user JSON).
- [x] Add `/api/settings/prompt-presets` GET/PATCH endpoints.
- [x] Update workflow run creation:
  - [x] Accept `prompt_preset_id` for `script` and `novel_to_script` runs
  - [x] Reject unsupported kinds using the field
  - [x] Persist the chosen id into `workflow_runs.state`
- [x] Update workflow executor:
  - [x] Resolve preset text per run kind (fallback to default preset)
  - [x] Inject preset `text` into `output_spec.script_format_notes`
  - [x] For `novel_to_script`, stop using Snapshot/Brief notes for conversion

## 3. Implementation (Web)

- [x] Add API client types + calls for prompt presets.
- [x] Settings tab: add two preset managers (script / novel→script):
  - [x] list presets
  - [x] add/edit/delete
  - [x] set default preset
- [x] Workflow creation UI:
  - [x] `script`: choose “剧本生成模板”
  - [x] `novel_to_script`: choose “小说→剧本模板”
- [x] Simplify preference UI: hide/remove `script_format` and “格式备注” as user-facing toggles.

## 4. Validation

- [x] Backend: run `pytest -q`.
- [x] Frontend: run `cd apps/web && npm run check`.
- [x] Run `openspec validate simplify-script-prompt-presets --strict`.
