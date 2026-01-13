# workflow-ide-interactions Specification

## Purpose
TBD - created by archiving change enhance-workflow-ide-interactions. Update Purpose after archive.
## Requirements
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

### Requirement: Intervene on a workflow node via chat
The system SHALL provide a chat-style interaction to apply changes to intermediate workflow state (outline, beats, draft, critic guidance, cursor) without manual JSON editing.

#### Scenario: Adjust outline via chat before continuing
- **GIVEN** a novel workflow run is at the outline or beats phase
- **WHEN** the user sends an intervention instruction (e.g., “加快第二幕节奏，增加一个更强的中点反转”)
- **THEN** the system SHALL update the workflow run state to reflect the change
- **AND** the user SHALL be able to continue stepwise execution from the updated state

