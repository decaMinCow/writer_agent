# Change: Add change propagation engine (edits → fact diffs → impact → repair)

## Why
User edits must be “refactor-safe”. When a user edits a chapter/scene, we need to:
- Extract factual changes (what is now true).
- Update derived knowledge (state/KG/open threads) accordingly.
- Identify impacted downstream artifacts and provide a one-click repair workflow.

## What Changes
- Backend:
  - Add “change extractor” that compares a base version and an edited version and emits structured patches.
  - Add persistence for propagation events + impacted artifacts.
  - Add APIs to preview changes, apply patches, and enqueue/trigger repairs.
- Frontend:
  - Show “change summary” + impacted items after an edit; offer a “repair” action.

## Impact
- Affected specs (new): `propagation-engine`
- Affected specs (update): `manage-artifacts`, `web-ui`
- Affected code: new DB tables + services; integrates with artifact editing

## Non-Goals (for this change)
- Perfect semantic diffs (MVP uses best-effort extraction)
- Full-fledged IDE refactor tooling (rename across all text, conflict resolution)

