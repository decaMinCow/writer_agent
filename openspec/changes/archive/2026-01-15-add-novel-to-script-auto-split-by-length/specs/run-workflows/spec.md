## MODIFIED Requirements

### Requirement: Configure novel→script run inputs at creation time
The system SHALL allow providing a source snapshot, a prompt preset, and a split mode when creating a `novel_to_script` workflow run.

#### Scenario: Create a novel→script run with a different source snapshot
- **GIVEN** two Snapshots exist for the same Brief
- **AND** the source snapshot has committed novel chapters
- **WHEN** the user creates a `novel_to_script` workflow run with `source_brief_snapshot_id` set to the source snapshot
- **THEN** the system SHALL create the run linked to the chosen `brief_snapshot_id`
- **AND** the system SHALL persist the source snapshot id in the run state for execution

#### Scenario: Create a novel→script run with a prompt preset
- **WHEN** the user creates a `novel_to_script` workflow run with `prompt_preset_id`
- **THEN** the system SHALL persist the chosen preset id in the workflow run state for later execution

#### Scenario: Create a novel→script run with a split mode
- **WHEN** the user creates a `novel_to_script` workflow run with `split_mode`
- **THEN** the system SHALL persist the chosen split mode in the workflow run state for later execution

#### Scenario: Missing split mode falls back to chapter-unit behavior
- **GIVEN** a novel→script workflow run is created without `split_mode`
- **WHEN** the workflow executes
- **THEN** the system SHALL behave as `1章=1集` by default

#### Scenario: Reject a source snapshot from another brief
- **GIVEN** a source snapshot exists but belongs to a different Brief than the run snapshot
- **WHEN** the user creates a `novel_to_script` run referencing that source snapshot
- **THEN** the system SHALL reject the request with an actionable error
