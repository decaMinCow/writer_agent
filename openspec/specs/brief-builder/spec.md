# brief-builder Specification

## Purpose
TBD - created by archiving change add-brief-builder-and-gap-checker. Update Purpose after archive.
## Requirements
### Requirement: Conversational Brief Builder
The system SHALL accept freeform user messages and update a Creative Brief draft as structured data.

#### Scenario: Update brief from a user message
- **WHEN** the user sends a message associated with an existing brief
- **THEN** the system SHALL persist the user message linked to that brief
- **AND** the system SHALL return an updated brief representation as structured JSON

### Requirement: Field-targeted edits via conversation
The system SHALL support messages that request partial updates to specific brief fields (e.g., tone, chapter count, antagonist motivation) without rewriting unrelated confirmed fields.

#### Scenario: User requests a targeted update
- **WHEN** the user message explicitly targets a brief field or section (e.g., “只改基调”)
- **THEN** the system SHALL apply changes only to the targeted field(s)
- **AND** previously confirmed unrelated fields SHALL remain unchanged

### Requirement: Output-spec driven configuration
The system SHALL store and use output specifications in the brief, including screenplay format preferences.

#### Scenario: Script format preference is set in the brief
- **WHEN** the user sets or updates screenplay formatting preference in the brief output specification
- **THEN** subsequent runs that snapshot the brief SHALL include that preference

