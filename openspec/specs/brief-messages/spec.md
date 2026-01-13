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

### Requirement: Stream brief message responses
The system SHALL provide a streaming API for brief messages so the client can show progress while the assistant response is being generated.

#### Scenario: Stream assistant output and finalize
- **WHEN** the client posts a brief message to the streaming endpoint
- **THEN** the system SHALL stream incremental assistant output events
- **AND** the system SHALL end the stream with a final payload equivalent to the non-stream response

