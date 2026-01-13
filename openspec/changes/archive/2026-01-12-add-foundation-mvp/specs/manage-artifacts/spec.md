## ADDED Requirements

### Requirement: Store versioned artifacts (chapters/scenes)
The system SHALL store user-visible artifacts (e.g., novel chapters and script scenes) with immutable version history.

#### Scenario: Create a new artifact version
- **WHEN** the user or an agent produces a new version of an artifact
- **THEN** the system SHALL persist the full artifact content and metadata as a new immutable version
- **AND** the system SHALL retain prior versions for audit and rollback

#### Scenario: Retrieve artifact versions
- **WHEN** the user requests the version history for an artifact
- **THEN** the system SHALL return the list of versions with creation timestamps and author/source metadata
- **AND** the user SHALL be able to retrieve any specific version by identifier

### Requirement: Associate artifacts with briefs and workflow runs
The system SHALL be able to associate artifacts and artifact versions with the brief snapshot and workflow run that produced them.

#### Scenario: View provenance for an artifact version
- **WHEN** the user views an artifact version
- **THEN** the system SHALL provide references to the producing workflow run and brief snapshot (when applicable)

