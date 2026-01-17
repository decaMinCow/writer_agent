## ADDED Requirements
### Requirement: UI provides one-click lint repair
The web UI SHALL provide a one-click action to repair snapshot lint issues by creating new versions, and present a summary of the results.

#### Scenario: Trigger repair from the lint panel
- **GIVEN** a Snapshot is selected
- **AND** lint issues exist for that snapshot
- **WHEN** the user clicks “一键修复”
- **THEN** the UI SHALL call the lint repair API
- **AND** the UI SHALL display a summary (repaired/skipped counts)

