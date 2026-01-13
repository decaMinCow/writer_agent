# execute-workflows Specification

## Purpose
TBD - created by archiving change add-generation-workflows. Update Purpose after archive.
## Requirements
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

### Requirement: Stepwise workflow execution supports novel→script
The system SHALL support stepwise execution for `WorkflowKind.novel_to_script`.

#### Scenario: Execute next step for novel→script
- **WHEN** a workflow run of kind `novel_to_script` executes the next step
- **THEN** the system SHALL advance its cursor and persist one step run output per call

### Requirement: Background autorun execution for workflow runs
The system SHALL support a server-driven “autorun” mode that repeatedly executes the next step until completion or cancellation.

#### Scenario: Start autorun for a run
- **GIVEN** a workflow run is in `queued` or `running`
- **WHEN** the user starts autorun
- **THEN** the system SHALL execute steps sequentially until the run reaches a terminal status or is paused/canceled

### Requirement: Stream workflow progress via SSE
The system SHALL stream workflow progress updates to clients using Server-Sent Events (SSE).

#### Scenario: Subscribe to run events
- **WHEN** a client subscribes to the run events stream
- **THEN** the system SHALL emit structured events for run/step state changes suitable for live UI updates

### Requirement: Forking preserves stepwise execution
Forked runs SHALL remain compatible with stepwise execution.

#### Scenario: Execute next step after forking
- **WHEN** a forked run executes the next step
- **THEN** the system SHALL continue from the forked state cursor without affecting the source run

