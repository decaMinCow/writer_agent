## ADDED Requirements

### Requirement: Fork workflow runs for alternative exploration
The system SHALL allow creating a new workflow run by forking the state of an existing run.

#### Scenario: Fork a run at a chosen step
- **GIVEN** a workflow run exists
- **WHEN** the user forks the run
- **THEN** the system SHALL create a new run with copied state and independent history

### Requirement: Perform targeted rewrites without full regeneration
The system SHALL support targeted rewrites that create new artifact versions while preserving provenance.

#### Scenario: Rewrite a specific span
- **GIVEN** an artifact version exists
- **WHEN** the user requests a targeted rewrite with instructions
- **THEN** the system SHALL create a new artifact version with the rewritten content and provenance metadata

