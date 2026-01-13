# web-ui Specification (Delta)

## ADDED Requirements
### Requirement: UI streams brief chat responses
The web UI SHALL display the assistant response incrementally while a brief chat message is in progress.

#### Scenario: Show typing updates during brief chat
- **WHEN** the user sends a brief chat message
- **THEN** the UI SHALL render streamed assistant deltas and prevent duplicate sends until completion

