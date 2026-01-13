## ADDED Requirements

### Requirement: Apply chat-based interventions to workflow run state
The system SHALL allow applying a natural-language intervention to a workflow run, producing a state patch that updates `workflow_runs.state` and is persisted for audit.

#### Scenario: Apply an intervention tied to a selected step
- **GIVEN** a workflow run exists with one or more step runs
- **WHEN** the user submits an intervention instruction referencing a chosen step
- **THEN** the system SHALL generate an assistant response and a `state_patch`
- **AND** the system SHALL apply the patch to the workflow run state
- **AND** the system SHALL record the intervention as a `workflow_step_runs` entry

