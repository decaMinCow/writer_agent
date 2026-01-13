# brief-messages Specification

## Purpose
TBD - created by archiving change add-brief-builder-and-gap-checker. Update Purpose after archive.
## Requirements
### Requirement: Persist brief conversation messages
The system SHALL persist brief-building conversation messages linked to a Creative Brief.

#### Scenario: Store and retrieve messages for a brief
- **WHEN** the user sends messages to build or edit a brief
- **THEN** the system SHALL store each message with timestamp and role metadata
- **AND** the user SHALL be able to retrieve the message history for that brief

