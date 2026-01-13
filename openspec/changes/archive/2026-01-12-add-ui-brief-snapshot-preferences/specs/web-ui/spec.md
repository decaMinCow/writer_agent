## ADDED Requirements

### Requirement: UI supports brief/snapshot creation and preference editing
The web UI SHALL allow the user to create Briefs and Snapshots and to edit preferences without using the raw API.

#### Scenario: Create brief and snapshot in UI
- **WHEN** the user creates a Brief and then creates a Snapshot from that Brief
- **THEN** the UI SHALL display the new Brief and Snapshot and allow starting workflows from the selected Snapshot

#### Scenario: Edit global defaults and per-brief overrides
- **WHEN** the user edits global defaults and then clears per-brief overrides
- **THEN** the effective preferences shown in the UI SHALL reflect global defaults

