# brief-snapshots Specification

## Purpose
TBD - created by archiving change add-ui-brief-snapshot-preferences. Update Purpose after archive.
## Requirements
### Requirement: Snapshot captures effective output spec
When creating a Brief Snapshot, the system SHALL store an effective `output_spec` derived from global defaults for preference fields.

#### Scenario: Create snapshot uses global defaults for preference keys
- **WHEN** a snapshot is created
- **THEN** the snapshot content SHALL include a fully-resolved `output_spec` based on global defaults for preference keys
- **AND** non-preference fields in `output_spec` (e.g., `chapter_count`) MAY be preserved from the Brief content

### Requirement: Delete a Brief Snapshot with cascade cleanup
The system SHALL allow deleting a Brief Snapshot and SHALL delete all data scoped to that Snapshot (workflow runs, artifact versions, and derived/indexed records).

#### Scenario: Delete a snapshot removes snapshot-scoped records
- **GIVEN** a Brief Snapshot exists
- **AND** the snapshot has workflow runs and artifacts/versions
- **WHEN** the user deletes the Snapshot
- **THEN** the system SHALL delete the Snapshot
- **AND** the system SHALL delete workflow runs and step runs linked to the Snapshot
- **AND** the system SHALL delete artifact versions linked to the Snapshot
- **AND** the system SHALL delete derived/index records linked to the Snapshot, including:
  - Memory/RAG chunks
  - Knowledge graph entities/relations/events
  - Story lint issues
  - Propagation events and impact markers
  - Open Threads and their refs
  - Snapshot glossary entries

