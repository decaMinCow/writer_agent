# web-ui Specification

## Purpose
TBD - created by archiving change add-ui-brief-snapshot-preferences. Update Purpose after archive.
## Requirements
### Requirement: UI supports brief/snapshot creation and preference editing
The web UI SHALL allow the user to create Briefs and Snapshots and to edit global preferences without using the raw API.

#### Scenario: Edit global defaults only
- **WHEN** the user edits global defaults
- **THEN** the UI SHALL show only global defaults and SHALL NOT present per-brief override controls
- **AND** the UI SHALL allow editing `auto_step_retries` and `auto_step_backoff_s` as part of global preferences

### Requirement: UI can create novel→script runs
The web UI SHALL allow the user to create and run `novel_to_script` workflow runs from a selected brief snapshot, and SHALL allow configuring source snapshot, prompt preset, and split mode at run creation time.

#### Scenario: Create a novel→script run
- **WHEN** the user selects a snapshot and chooses “小说→剧本”
- **THEN** the UI SHALL create a workflow run and allow stepwise execution

#### Scenario: Select a prompt preset (or use default) when creating a novel→script run
- **GIVEN** prompt presets exist in Settings
- **WHEN** the user creates a novel→script run without choosing a preset explicitly
- **THEN** the UI SHALL omit `prompt_preset_id` so the backend can apply the global default preset

#### Scenario: Select auto-splitting when creating a novel→script run
- **WHEN** the user chooses “按字数自动拆集（动态）” for a novel→script run
- **THEN** the UI SHALL create the run with `split_mode=auto_by_length`

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

#### Scenario: Show novel→script episode progress label
- **GIVEN** a novel→script workflow run has cursor phase `nts_episode_draft` and `chapter_index=3`
- **WHEN** the UI renders the workflow run list
- **THEN** the run SHALL be labeled similar to `小说→剧本 · 第3集 · 草稿`

#### Scenario: Show episode breakdown label
- **GIVEN** a novel→script workflow run has cursor phase `nts_episode_breakdown` and `chapter_index=1`
- **WHEN** the UI renders the workflow run list
- **THEN** the run SHALL be labeled similar to `小说→剧本 · 第1集 · 拆解`

#### Scenario: Show auto-split label using script episode index (not chapter index)
- **GIVEN** a novel→script workflow run is in `split_mode=auto_by_length`
- **AND** the cursor includes a `episode_index` representing the current script episode being drafted
- **WHEN** the UI renders the workflow run list
- **THEN** the run SHOULD be labeled similar to `小说→剧本 · 第12集 · 草稿`
- **AND** the UI SHOULD expose the source `chapter_index` as secondary context (e.g. `（章3）`)

### Requirement: UI supports workflow node intervention chat
The web UI SHALL provide a “节点对话干预” panel when a workflow run is selected, allowing the user to send an instruction and apply the resulting state patch.

#### Scenario: Send an intervention from the UI
- **GIVEN** a workflow run is selected in the UI
- **WHEN** the user sends an intervention instruction
- **THEN** the UI SHALL call the intervention API
- **AND** the UI SHALL refresh run state and step history

### Requirement: UI can configure global novel→script prompt defaults
The web UI SHALL provide an editor for the global novel→script prompt defaults.

#### Scenario: Edit global novel→script prompt defaults
- **WHEN** the user edits and saves the global novel→script prompt defaults in the UI
- **THEN** the UI SHALL persist the value via the settings API

### Requirement: UI manages global prompt preset catalogs
The web UI SHALL allow the user to manage global prompt preset catalogs for direct script generation and novel→script conversion.

#### Scenario: Edit prompt presets in settings
- **WHEN** the user adds/edits/deletes presets and sets the default preset in the Settings tab
- **THEN** the UI SHALL persist changes via the settings API

### Requirement: UI selects a prompt preset when creating script/novel→script runs
The web UI SHALL allow selecting a prompt preset when creating `script` and `novel_to_script` workflow runs.

#### Scenario: Create a script run with a selected preset
- **WHEN** the user selects “剧本” and chooses a prompt preset
- **THEN** the UI SHALL create a workflow run with `prompt_preset_id`

### Requirement: Right pane groups content into Project / Assets / Settings
The UI SHALL provide a clear separation of right-pane content into three groups so that project management, story assets, and global settings are not mixed in a single long scroll.

#### Scenario: Switch right pane tabs
- **GIVEN** the user is using the IDE UI
- **WHEN** the user selects a right-pane tab (Project / Assets / Settings)
- **THEN** the UI SHALL show only the panels relevant to that group
- **AND** the UI SHOULD remember the last selected tab locally for the next visit

### Requirement: UI uses Chinese labels for user-facing workflow and asset terms
The UI SHALL present user-facing labels in Chinese for common workflow and asset concepts.

#### Scenario: Translate workflow labels and statuses
- **WHEN** the UI renders workflow runs, steps, and controls
- **THEN** the UI SHALL display Chinese labels for names and statuses (while preserving internal enum values)

#### Scenario: Translate common configuration field labels
- **WHEN** the UI renders provider and preference settings
- **THEN** labels such as `Base URL`, `Chat Model`, `Embeddings Model`, `Timeout`, `Max Retries`, and `default` SHALL be displayed as clear Chinese equivalents

### Requirement: UI provides contextual help text for advanced panels
The UI SHALL provide short, grey helper text (and/or an expand/collapse help block) for panels that require user knowledge, so the user can understand what the feature does and how to use it.

#### Scenario: Open Threads panel explains usage with an example
- **GIVEN** the user opens the Open Threads (伏笔/线索) panel
- **THEN** the UI SHALL explain what a thread is, how to create one, and how to add references
- **AND** the UI SHALL explain the meaning of `introduced/reinforced/resolved` with a short example workflow

#### Scenario: KG/Lint panel explains when to run and how to jump
- **GIVEN** the user opens the KG/Lint panel
- **THEN** the UI SHALL explain the difference between “重建/运行” actions and the expected result
- **AND** the UI SHALL explain that clicking an issue can jump to the referenced artifact version (when available)

### Requirement: UI provides one-click lint repair
The web UI SHALL provide a one-click action to repair snapshot lint issues by creating new versions, and present a summary of the results.

#### Scenario: Trigger repair from the lint panel
- **GIVEN** a Snapshot is selected
- **AND** lint issues exist for that snapshot
- **WHEN** the user clicks “一键修复”
- **THEN** the UI SHALL call the lint repair API
- **AND** the UI SHALL display a summary (repaired/skipped counts)

