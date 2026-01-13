## MODIFIED Requirements

### Requirement: Store versioned artifacts (chapters/scenes)
The system SHALL store user-visible artifacts (e.g., novel chapters and script scenes) with immutable version history, including user-authored edits.

#### Scenario: Save a user edit as a new version
- **GIVEN** an existing artifact version exists
- **WHEN** the user edits the content in the IDE and saves
- **THEN** the system SHALL persist the edited text as a new immutable artifact version with `source=user`
- **AND** the system SHALL retain prior versions for audit and rollback

