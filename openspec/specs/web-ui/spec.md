# web-ui Specification

## Purpose
TBD - created by archiving change add-ui-brief-snapshot-preferences. Update Purpose after archive.
## Requirements
### Requirement: UI supports brief/snapshot creation and preference editing
The web UI SHALL allow the user to create Briefs and Snapshots and to edit preferences without using the raw API.

#### Scenario: Create brief and snapshot in UI
- **WHEN** the user creates a Brief and then creates a Snapshot from that Brief
- **THEN** the UI SHALL display the new Brief and Snapshot and allow starting workflows from the selected Snapshot

#### Scenario: Edit global defaults and per-brief overrides
- **WHEN** the user edits global defaults and then clears per-brief overrides
- **THEN** the effective preferences shown in the UI SHALL reflect global defaults

### Requirement: UI can create novel→script runs
The web UI SHALL allow the user to create and run `novel_to_script` workflow runs from a selected brief snapshot.

#### Scenario: Create a novel→script run
- **WHEN** the user selects a snapshot and chooses “小说→剧本”
- **THEN** the UI SHALL create a workflow run and allow stepwise execution

### Requirement: UI shows live workflow progress without polling
The web UI SHALL display live workflow progress updates using SSE.

#### Scenario: Observe autorun progress in UI
- **WHEN** the user starts autorun for a workflow run
- **THEN** the UI SHALL update step status and outputs as events arrive

### Requirement: UI shows knowledge and lint panels
The web UI SHALL provide basic panels to view Knowledge Graph entities and lint issues for a selected snapshot.

#### Scenario: Navigate from issue to artifact version
- **WHEN** the user clicks a lint issue referencing an artifact version
- **THEN** the UI SHALL navigate to or highlight the referenced artifact/version content

### Requirement: UI supports propagation preview and repair
The web UI SHALL present a propagation summary after edits and allow one-click repair actions.

#### Scenario: Repair impacted items
- **WHEN** the user clicks “repair” for impacted artifacts
- **THEN** the UI SHALL create repaired artifact versions and update the impacted status

### Requirement: UI supports Open Threads panel
The web UI SHALL provide an Open Threads panel that shows open/closed threads and their references.

#### Scenario: Jump from thread to referenced version
- **WHEN** the user selects a thread reference
- **THEN** the UI SHALL show the referenced artifact version content

### Requirement: UI supports fork and targeted rewrite
The web UI SHALL provide controls to fork runs and perform targeted rewrites of artifacts.

#### Scenario: Fork from the UI
- **WHEN** the user clicks “fork” on a run
- **THEN** the UI SHALL create a new run and display it alongside existing runs

### Requirement: UI supports exporting deliverables
The web UI SHALL provide export actions for a selected snapshot.

#### Scenario: Download an export from the UI
- **WHEN** the user clicks an export action
- **THEN** the UI SHALL download the generated file and report errors if export fails

