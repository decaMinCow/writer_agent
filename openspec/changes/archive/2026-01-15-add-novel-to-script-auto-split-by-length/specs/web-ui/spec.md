## MODIFIED Requirements

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
