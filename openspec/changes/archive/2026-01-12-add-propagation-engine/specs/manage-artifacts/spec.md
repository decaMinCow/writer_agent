## ADDED Requirements

### Requirement: Track impacts of edits on downstream artifacts
The system SHALL be able to mark artifacts/versions as “impacted” by a change and surface this status to the UI.

#### Scenario: Impact markers after edit
- **WHEN** a propagation event is applied
- **THEN** the system SHALL persist impact markers that identify which artifacts are affected and why

