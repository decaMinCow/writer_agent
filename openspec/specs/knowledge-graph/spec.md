# knowledge-graph Specification

## Purpose
TBD - created by archiving change add-knowledge-graph-and-story-linter. Update Purpose after archive.
## Requirements
### Requirement: Persist a snapshot-scoped knowledge graph
The system SHALL persist a Knowledge Graph scoped by `brief_snapshot_id` that represents story entities and relations.

#### Scenario: Store entities and relations for a snapshot
- **WHEN** the system indexes story knowledge for a brief snapshot
- **THEN** it SHALL persist entities and relations that can be queried by snapshot and entity identifiers

### Requirement: Query knowledge graph for inspection
The system SHALL provide API access to query entities, relations, and event references for a given snapshot.

#### Scenario: Retrieve entities for a snapshot
- **WHEN** the user requests KG entities for a snapshot
- **THEN** the system SHALL return a list of entities with stable identifiers and metadata

