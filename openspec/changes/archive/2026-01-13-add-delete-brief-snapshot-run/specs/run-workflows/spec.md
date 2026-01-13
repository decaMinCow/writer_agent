## ADDED Requirements

### Requirement: Delete a workflow run and its produced content
The system SHALL allow deleting a workflow run and SHALL delete the run history (step runs) and any content produced by that run (including artifact versions and dependent records).

#### Scenario: Delete a workflow run removes its step history and versions
- **GIVEN** a workflow run exists
- **AND** the run has one or more step runs
- **AND** the run produced one or more artifact versions
- **WHEN** the user deletes the workflow run
- **THEN** the system SHALL delete the workflow run
- **AND** the system SHALL delete its step runs
- **AND** the system SHALL delete artifact versions produced by the run
- **AND** the system SHALL delete any records that reference those deleted versions (e.g., memory chunks, KG events, lint issues, open thread refs, propagation events/impacts)

