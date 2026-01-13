## ADDED Requirements

### Requirement: Stepwise workflow execution
The system SHALL support stepwise execution of workflow runs such that a user or UI can execute exactly one next step at a time.

#### Scenario: Execute the next step
- **WHEN** the user requests execution of the next step for a workflow run
- **THEN** the system SHALL execute exactly one step and persist a step run record with status and outputs
- **AND** the workflow run SHALL update its state/cursor so the next call continues from the correct position

#### Scenario: Auto mode loops over next-step execution
- **WHEN** the user enables auto mode in the UI
- **THEN** the UI SHALL be able to repeatedly execute next-step calls until the run is completed or paused/failed

### Requirement: Pause and resume workflow execution
The system SHALL allow a workflow run to be paused and later resumed without losing persisted intermediate outputs.

#### Scenario: Pause a running workflow
- **WHEN** the user pauses a workflow run
- **THEN** the system SHALL set the workflow run status to `paused`

#### Scenario: Resume a paused workflow
- **WHEN** the user resumes a paused workflow run
- **THEN** the system SHALL continue execution from the last completed step

