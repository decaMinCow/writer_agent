# Design: Propagation engine (MVP)

## Inputs
- `base_artifact_version_id`
- `edited_artifact_version_id` (typically `source=user`)

## Outputs (structured)
- `fact_changes`: human-readable summary
- `brief_patch`: JSON merge patch (optional)
- `kg_patch`: adds/removes/renames entities/relations/events (optional)
- `open_threads_patch`: thread updates (optional)
- `impact_report`: list of impacted artifacts/versions with reasons

## Storage
- `propagation_events`: snapshot-scoped event sourcing for propagation (audit + rollback later)
- `artifact_impacts`: links impacted artifacts/versions to a propagation event

## Repair strategy (MVP)
- Repair is explicit:
  - Mark impacted artifacts as “needs repair”.
  - Provide a “repair run” action that generates new versions for selected impacted artifacts.
- Automatic bulk regeneration policies can be expanded later.

