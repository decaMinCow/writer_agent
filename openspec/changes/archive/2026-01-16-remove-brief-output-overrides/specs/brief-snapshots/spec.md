## MODIFIED Requirements
### Requirement: Snapshot captures effective output spec
When creating a Brief Snapshot, the system SHALL store an effective `output_spec` derived from global defaults for preference fields.

#### Scenario: Create snapshot uses global defaults for preference keys
- **WHEN** a snapshot is created
- **THEN** the snapshot content SHALL include a fully-resolved `output_spec` based on global defaults for preference keys
- **AND** non-preference fields in `output_spec` (e.g., `chapter_count`) MAY be preserved from the Brief content
