# execute-workflows (delta)

## ADDED Requirements

### Requirement: Live execution preferences apply to existing runs
The system SHALL allow updating workflow execution preferences that control reliability/automation without requiring creation of a new Snapshot.

The following `output_spec` keys SHALL be treated as runtime execution knobs:
- `max_fix_attempts`
- `auto_step_retries`
- `auto_step_backoff_s`

#### Scenario: Update preferences affects a run from the next step
- **GIVEN** a workflow run exists for a snapshot
- **AND** the run is not yet finished
- **WHEN** the user updates global defaults or per-brief overrides for `max_fix_attempts`
- **THEN** the next executed step (or fix loop decision) SHALL use the updated `max_fix_attempts`

#### Scenario: Update autorun retry policy affects the next retry decision
- **GIVEN** autorun is executing a workflow run
- **AND** the next step fails with a retryable error
- **WHEN** the user updates global defaults or per-brief overrides for `auto_step_retries` / `auto_step_backoff_s`
- **THEN** the next retry scheduling decision SHALL use the updated retry count/backoff values

## MODIFIED Requirements

### Requirement: Background autorun execution for workflow runs
The system SHALL support a server-driven “autorun” mode that repeatedly executes the next step until completion or cancellation.

#### Scenario: Autorun auto-retries retryable failures
- **GIVEN** autorun is running for a workflow run
- **AND** the next step fails with a retryable error (e.g., transient connection error or output parse/validation error)
- **WHEN** the system applies the autorun retry policy
- **THEN** the system SHALL schedule a retry of the same step after a backoff delay
- **AND** the retry policy SHALL be resolved from the latest global defaults merged with per-brief overrides (not only the snapshot-captured values)
- **AND** the system SHALL NOT require user intervention to continue autorun
- **AND** the system SHALL stop autorun and leave the run in a failed state once the retry limit is exhausted
