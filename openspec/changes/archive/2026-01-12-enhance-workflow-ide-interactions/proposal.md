# Change: Enhance workflow IDE interactions (edit, fork, targeted rewrite)

## Why
To make the product feel like an IDE (not a chatbox), the workflow UI needs richer interaction:
- Edit intermediate artifacts (outline/beats/state) and resume from there.
- Fork runs to explore alternatives without losing history.
- Targeted rewrites without regenerating everything.

## What Changes
- Backend:
  - Add “fork run” API to create a new run from an existing run state at a chosen point.
  - Add targeted rewrite endpoints that create new artifact versions with provenance.
- Frontend:
  - Add UI controls to fork, edit-and-resume, and targeted rewrite.

## Impact
- Affected specs (new): `workflow-ide-interactions`
- Affected specs (update): `execute-workflows`, `web-ui`

## Non-Goals (for this change)
- Full visual diff/merge tooling
- Multi-user collaboration features

