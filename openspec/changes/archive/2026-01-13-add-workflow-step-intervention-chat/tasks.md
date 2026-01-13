## 1. Spec + Validation
- [x] Draft spec deltas for run/step intervention chat
- [x] `openspec validate add-workflow-step-intervention-chat --strict`

## 2. Backend (FastAPI)
- [x] Add prompt templates for workflow intervention (system/user)
- [x] Add Pydantic schemas for intervention request/response
- [x] Add `POST /api/workflow-runs/{run_id}/interventions` endpoint
- [x] Record each intervention as a `workflow_step_runs` row with outputs containing messages + applied patch
- [x] Add tests for: applies patch, records step run, validates run/step relationship

## 3. Frontend (SvelteKit)
- [x] Add API client helper for interventions
- [x] Add “节点对话干预” panel under selected run (uses selected step as context when available)
- [x] Show intervention history from step runs (`step_name == "intervention"`)

## 4. Verification + Archive
- [x] `cd apps/api && uv run pytest`
- [x] `cd apps/web && npm run check`
- [x] Mark all tasks as complete
- [x] Archive via `openspec archive add-workflow-step-intervention-chat --yes` and validate specs
