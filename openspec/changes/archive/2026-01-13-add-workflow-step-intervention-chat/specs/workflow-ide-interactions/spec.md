## ADDED Requirements

### Requirement: Intervene on a workflow node via chat
The system SHALL provide a chat-style interaction to apply changes to intermediate workflow state (outline, beats, draft, critic guidance, cursor) without manual JSON editing.

#### Scenario: Adjust outline via chat before continuing
- **GIVEN** a novel workflow run is at the outline or beats phase
- **WHEN** the user sends an intervention instruction (e.g., “加快第二幕节奏，增加一个更强的中点反转”)
- **THEN** the system SHALL update the workflow run state to reflect the change
- **AND** the user SHALL be able to continue stepwise execution from the updated state

