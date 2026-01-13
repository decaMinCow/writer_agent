## ADDED Requirements

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

