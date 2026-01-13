## ADDED Requirements

### Requirement: Background autorun execution for workflow runs
The system SHALL support a server-driven “autorun” mode that repeatedly executes the next step until completion or cancellation.

#### Scenario: Start autorun for a run
- **GIVEN** a workflow run is in `queued` or `running`
- **WHEN** the user starts autorun
- **THEN** the system SHALL execute steps sequentially until the run reaches a terminal status or is paused/canceled

### Requirement: Stream workflow progress via SSE
The system SHALL stream workflow progress updates to clients using Server-Sent Events (SSE).

#### Scenario: Subscribe to run events
- **WHEN** a client subscribes to the run events stream
- **THEN** the system SHALL emit structured events for run/step state changes suitable for live UI updates

