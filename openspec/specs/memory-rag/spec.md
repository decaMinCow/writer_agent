# memory-rag Specification

## Purpose
TBD - created by archiving change add-generation-workflows. Update Purpose after archive.
## Requirements
### Requirement: Store and retrieve story memory via embeddings
The system SHALL store committed story text as retrievable memory chunks and support similarity retrieval for generation steps.

#### Scenario: Index committed text (including user edits)
- **WHEN** an artifact version is created with a `brief_snapshot_id`
- **AND** embeddings are configured
- **THEN** the system SHALL store one or more memory chunks linked to that artifact version for retrieval

