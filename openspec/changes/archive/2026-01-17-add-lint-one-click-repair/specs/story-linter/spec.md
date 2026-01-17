## ADDED Requirements
### Requirement: Repair lint issues by creating new versions
The system SHALL provide a batch repair action for lint issues that reference a specific artifact version, creating repaired artifact versions without deleting the originals.

#### Scenario: Repair issues for a snapshot
- **GIVEN** a snapshot has lint issues
- **AND** some issues reference an `artifact_version_id`
- **WHEN** the user triggers a lint repair for the snapshot
- **THEN** the system SHALL create new artifact versions for the referenced artifacts
- **AND** the system SHALL return a summary that includes counts for repaired and skipped issues

