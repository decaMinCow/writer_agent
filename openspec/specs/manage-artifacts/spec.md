# manage-artifacts Specification

## Purpose
TBD - created by archiving change add-foundation-mvp. Update Purpose after archive.
## Requirements
### Requirement: Store versioned artifacts (chapters/scenes)
The system SHALL store user-visible artifacts (e.g., novel chapters and script scenes) with immutable version history, including user-authored edits.

#### Scenario: Save a user edit as a new version
- **GIVEN** an existing artifact version exists
- **WHEN** the user edits the content in the IDE and saves
- **THEN** the system SHALL persist the edited text as a new immutable artifact version with `source=user`
- **AND** the system SHALL retain prior versions for audit and rollback

### Requirement: Associate artifacts with briefs and workflow runs
The system SHALL be able to associate artifacts and artifact versions with the brief snapshot and workflow run that produced them.

#### Scenario: View provenance for an artifact version
- **WHEN** the user views an artifact version
- **THEN** the system SHALL provide references to the producing workflow run and brief snapshot (when applicable)

### Requirement: Track impacts of edits on downstream artifacts
The system SHALL be able to mark artifacts/versions as “impacted” by a change and surface this status to the UI.

#### Scenario: Impact markers after edit
- **WHEN** a propagation event is applied
- **THEN** the system SHALL persist impact markers that identify which artifacts are affected and why

