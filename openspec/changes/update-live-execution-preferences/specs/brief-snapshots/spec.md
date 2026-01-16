# brief-snapshots (delta)

## MODIFIED Requirements

### Requirement: Snapshot captures effective output spec
When creating a Brief Snapshot, the system SHALL store an effective `output_spec` by merging global defaults with per-brief overrides.

#### Scenario: Create snapshot stores resolved output_spec
- **WHEN** a snapshot is created for a Brief that has partial output spec overrides
- **THEN** the snapshot content SHALL include a fully-resolved `output_spec` suitable for workflow execution
- **AND** the snapshot’s resolved `output_spec` SHALL be treated as the baseline for “creative” output constraints
- **AND** the runtime execution knobs (`max_fix_attempts`, `auto_step_retries`, `auto_step_backoff_s`) MAY be overridden at execution time by the latest global/brief preferences
