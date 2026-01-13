# brief-messages Specification (Delta)

## ADDED Requirements
### Requirement: Stream brief message responses
The system SHALL provide a streaming API for brief messages so the client can show progress while the assistant response is being generated.

#### Scenario: Stream assistant output and finalize
- **WHEN** the client posts a brief message to the streaming endpoint
- **THEN** the system SHALL stream incremental assistant output events
- **AND** the system SHALL end the stream with a final payload equivalent to the non-stream response

