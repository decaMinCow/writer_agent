## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: UI can create novel→script runs
The web UI SHALL allow the user to create and run `novel_to_script` workflow runs from a selected brief snapshot, and SHALL allow configuring source snapshot and prompt preset at run creation time.

#### Scenario: Create a novel→script run
- **WHEN** the user selects a snapshot and chooses “小说→剧本”
- **THEN** the UI SHALL create a workflow run and allow stepwise execution

#### Scenario: Select a prompt preset (or use default) when creating a novel→script run
- **GIVEN** prompt presets exist in Settings
- **WHEN** the user creates a novel→script run without choosing a preset explicitly
- **THEN** the UI SHALL omit `prompt_preset_id` so the backend can apply the global default preset
