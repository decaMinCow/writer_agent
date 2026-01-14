# web-ui Specification

## Purpose
TBD - created by archiving change add-ui-brief-snapshot-preferences. Update Purpose after archive.
## Requirements
### Requirement: UI supports brief/snapshot creation and preference editing
The web UI SHALL allow the user to create Briefs and Snapshots and to edit preferences without using the raw API.

#### Scenario: Edit global defaults and per-brief overrides
- **WHEN** the user edits global defaults and then clears per-brief overrides
- **THEN** the effective preferences shown in the UI SHALL reflect global defaults
- **AND** the UI SHALL allow editing `auto_step_retries` and `auto_step_backoff_s` as part of preferences

### Requirement: UI can create novel→script runs
The web UI SHALL allow the user to create and run `novel_to_script` workflow runs from a selected brief snapshot, and SHALL allow configuring source snapshot and conversion rules at run creation time.

#### Scenario: Create a novel→script run
- **WHEN** the user selects a snapshot and chooses “小说→剧本”
- **THEN** the UI SHALL create a workflow run and allow stepwise execution

#### Scenario: Create a novel→script run with source snapshot and conversion notes
- **GIVEN** the user selects “小说→剧本”
- **WHEN** the user selects a novel source Snapshot (may differ from the run Snapshot)
- **AND** the user enters conversion notes (e.g., short-drama formatting rules)
- **THEN** the UI SHALL create the run with `source_brief_snapshot_id` and `conversion_output_spec` populated

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

### Requirement: UI can configure model provider settings
The web UI SHALL provide a panel to view and update the OpenAI-compatible provider settings used by the backend.

#### Scenario: Save provider settings in the UI
- **WHEN** the user enters a base URL and API key and clicks save
- **THEN** the UI SHALL persist the settings via the API and indicate that an API key is configured

#### Scenario: Clear provider API key in the UI
- **WHEN** the user clears the stored key
- **THEN** the UI SHALL show the provider as unconfigured and report errors from LLM-backed features

### Requirement: UI streams brief chat responses
The web UI SHALL display the assistant response incrementally while a brief chat message is in progress.

#### Scenario: Show typing updates during brief chat
- **WHEN** the user sends a brief chat message
- **THEN** the UI SHALL render streamed assistant deltas and prevent duplicate sends until completion

### Requirement: UI shows Brief → Snapshot → Run hierarchy
The web UI SHALL present a hierarchical view where selecting a Brief narrows the visible Snapshots, and selecting a Snapshot narrows the visible Workflow Runs.

#### Scenario: Filter runs by selected snapshot
- **GIVEN** multiple Briefs exist and each has Snapshots
- **AND** multiple workflow runs exist across Snapshots
- **WHEN** the user selects a Snapshot
- **THEN** the UI SHALL show only the workflow runs whose `brief_snapshot_id` matches the selected Snapshot

### Requirement: UI supports deleting Briefs, Snapshots, and Runs
The web UI SHALL provide delete actions for Briefs, Snapshots, and Workflow Runs, with user confirmation.

#### Scenario: Confirm and delete a snapshot from UI
- **GIVEN** a Snapshot is selected in the UI
- **WHEN** the user confirms deletion
- **THEN** the UI SHALL call the delete API
- **AND** the UI SHALL refresh lists and clear selections that referenced deleted items

### Requirement: UI displays workflow runs with Chinese, phase-aware names
The web UI SHALL display workflow run list items using Chinese labels derived from workflow kind and current cursor phase/index.

#### Scenario: Show novel chapter progress label
- **GIVEN** a novel workflow run has cursor phase `novel_chapter_draft` and `chapter_index=3`
- **WHEN** the UI renders the workflow run list
- **THEN** the run SHALL be labeled similar to `小说 · 第3章 · 草稿`

### Requirement: UI supports workflow node intervention chat
The web UI SHALL provide a “节点对话干预” panel when a workflow run is selected, allowing the user to send an instruction and apply the resulting state patch.

#### Scenario: Send an intervention from the UI
- **GIVEN** a workflow run is selected in the UI
- **WHEN** the user sends an intervention instruction
- **THEN** the UI SHALL call the intervention API
- **AND** the UI SHALL refresh run state and step history

