## 1. Implementation
- [x] 1.1 Add prompt templates for novel→script scene list, draft, critic (fidelity-focused)
- [x] 1.2 Implement `novel_to_script` phases in workflow executor (scene_list → per-scene loop → commit)
- [x] 1.3 Update `/api/workflow-runs/{id}/next` default step_name for `novel_to_script`
- [x] 1.4 Web: enable creating `novel_to_script` runs (remove “未实现” block) and keep step runner UX
- [x] 1.5 Add tests: source selection (latest per chapter), missing-source failure, happy-path run, format honoring

## 2. Validation
- [x] 2.1 `openspec validate add-novel-to-script-workflow --strict`
- [x] 2.2 Backend: `ruff` + `pytest`
- [x] 2.3 Frontend: `npm run lint` + `npm run check`
