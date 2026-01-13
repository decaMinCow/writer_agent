## ADDED Requirements

### Requirement: Persist CurrentState as structured JSON
The system SHALL persist CurrentState as structured JSON and use it as a hard constraint for subsequent generation steps.

#### Scenario: State is used as constraint
- **WHEN** a generation step runs after prior commits
- **THEN** the step input SHALL include the current state
- **AND** the step MUST NOT violate hard constraints encoded in state

