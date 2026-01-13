# Design: Knowledge Graph + story linter (MVP)

## Why Postgres is acceptable (MVP)
- Our queries are mostly snapshot-scoped lookups, filters, and simple traversals (1–2 hops).
- Postgres tables with proper indexes are sufficient and simpler to operate.
- We will introduce a `KgStore` service interface so swapping to Neo4j later does not require rewriting the product logic.

## Data model (sketch)
- `kg_entities`: `id`, `brief_snapshot_id`, `name`, `type`, `meta`
- `kg_relations`: `id`, `brief_snapshot_id`, `subject_entity_id`, `predicate`, `object_entity_id`, `meta`
- `kg_events`: `id`, `brief_snapshot_id`, `event_key`, `summary`, `time_hint`, `artifact_version_id`, `meta`
- `lint_issues`: `id`, `brief_snapshot_id`, `severity`, `code`, `message`, `artifact_version_id`, `meta`

## Linter rules (MVP)
Hard rules (block/flag):
- Dead character appears again
- Character presence conflict (in two places at once, same time window)
- Inventory impossible (uses item not acquired)
Soft rules (warn):
- POV drift
- OOC tendencies (best-effort rubric)

## Extraction
- MVP uses an LLM JSON schema extractor to emit entities/relations/events from an artifact version.
- The extractor can be re-run after user edits.

