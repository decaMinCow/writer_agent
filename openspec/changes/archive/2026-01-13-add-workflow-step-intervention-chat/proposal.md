# Change: Add workflow step intervention chat

## Why
Editing `run.state` JSON manually is powerful but error-prone. We want a simpler “human-in-the-loop” way to intervene on a workflow node (outline / beats / draft / critic results / cursor) using natural language instructions.

## What Changes
- Add an API endpoint to apply a **chat-based intervention** to a workflow run:
  - The user provides an instruction (and optionally which step they are targeting).
  - The backend uses the configured LLM to generate an `assistant_message` and a `state_patch`.
  - The backend applies the patch to `workflow_runs.state` and records the intervention as a `workflow_step_runs` entry.
- Add a UI panel under the workflow area for “节点对话干预”:
  - Shows prior intervention records (from step runs)
  - Lets the user send an instruction tied to the selected step/run
  - Refreshes run state + steps after the intervention is applied

## Impact
- Affected specs: `run-workflows`, `workflow-ide-interactions`, `web-ui`
- Affected backend: `apps/api/app/api/routers/workflows.py`, new prompt templates and intervention service
- Affected frontend: `apps/web/src/routes/+page.svelte`, `apps/web/src/lib/api.ts`

## Non-Goals
- Full multi-turn workflow chat memory beyond what is stored as step runs (MVP uses step history).
- Streaming token-by-token updates for interventions (may be added later; MVP uses request/response + loading state).

