## ADDED Requirements

### Requirement: Stepwise workflow execution supports novel→script
The system SHALL support stepwise execution for `WorkflowKind.novel_to_script`.

#### Scenario: Execute next step for novel→script
- **WHEN** a workflow run of kind `novel_to_script` executes the next step
- **THEN** the system SHALL advance its cursor and persist one step run output per call
