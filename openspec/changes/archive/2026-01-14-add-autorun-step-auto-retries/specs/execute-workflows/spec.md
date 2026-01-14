# execute-workflows — Delta (add-autorun-step-auto-retries)

## MODIFIED Requirements

### Requirement: Background autorun execution for workflow runs
The system SHALL support a server-driven “autorun” mode that repeatedly executes the next step until completion or cancellation.

#### Scenario: Start autorun for a run
- **GIVEN** a workflow run is in `queued` or `running`
- **WHEN** the user starts autorun
- **THEN** the system SHALL execute steps sequentially until the run reaches a terminal status or is paused/canceled

#### Scenario: Autorun auto-retries retryable failures
- **GIVEN** autorun is running for a workflow run
- **AND** the next step fails with a retryable error (e.g., transient connection error or output parse/validation error)
- **WHEN** the system applies the autorun retry policy
- **THEN** the system SHALL schedule a retry of the same step after a backoff delay
- **AND** the system SHALL NOT require user intervention to continue autorun
- **AND** the system SHALL stop autorun and leave the run in a failed state once the retry limit is exhausted

