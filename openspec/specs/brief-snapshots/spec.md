# brief-snapshots Specification

## Purpose
TBD - created by archiving change add-ui-brief-snapshot-preferences. Update Purpose after archive.
## Requirements
### Requirement: Snapshot captures effective output spec
When creating a Brief Snapshot, the system SHALL store an effective `output_spec` by merging global defaults with per-brief overrides.

#### Scenario: Create snapshot stores resolved output_spec
- **WHEN** a snapshot is created for a Brief that has partial output spec overrides
- **THEN** the snapshot content SHALL include a fully-resolved `output_spec` suitable for workflow execution

