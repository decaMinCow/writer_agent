## ADDED Requirements

### Requirement: Delete a Brief and all contained data
The system SHALL allow deleting a Brief and SHALL delete all data contained under that Brief (including snapshots, messages, workflow runs, artifacts/versions, and derived/indexed records).

#### Scenario: Delete a brief with snapshots and runs
- **GIVEN** a Brief exists with one or more Snapshots and messages
- **AND** one or more workflow runs and artifacts were produced from those Snapshots
- **WHEN** the user deletes the Brief
- **THEN** the system SHALL delete the Brief
- **AND** the system SHALL delete all Snapshots linked to that Brief
- **AND** the system SHALL delete all snapshot-scoped data as defined in `brief-snapshots`

