## ADDED Requirements

### Requirement: UI shows live workflow progress without polling
The web UI SHALL display live workflow progress updates using SSE.

#### Scenario: Observe autorun progress in UI
- **WHEN** the user starts autorun for a workflow run
- **THEN** the UI SHALL update step status and outputs as events arrive

