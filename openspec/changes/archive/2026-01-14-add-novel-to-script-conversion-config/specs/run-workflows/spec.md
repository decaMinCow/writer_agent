# run-workflows — Delta (add-novel-to-script-conversion-config)

## ADDED Requirements

### Requirement: Configure novel→script run inputs at creation time
The system SHALL allow providing a source snapshot and conversion output spec when creating a `novel_to_script` workflow run.

#### Scenario: Create a novel→script run with a different source snapshot
- **GIVEN** two Snapshots exist for the same Brief
- **AND** the source snapshot has committed novel chapters
- **WHEN** the user creates a `novel_to_script` workflow run with `source_brief_snapshot_id` set to the source snapshot
- **THEN** the system SHALL create the run linked to the chosen `brief_snapshot_id`
- **AND** the system SHALL persist the source snapshot id in the run state for execution

#### Scenario: Create a novel→script run with conversion output spec
- **WHEN** the user creates a `novel_to_script` workflow run with a `conversion_output_spec`
- **THEN** the system SHALL persist the conversion output spec in the run state for execution

#### Scenario: Reject a source snapshot from another brief
- **GIVEN** a source snapshot exists but belongs to a different Brief than the run snapshot
- **WHEN** the user creates a `novel_to_script` run referencing that source snapshot
- **THEN** the system SHALL reject the request with an actionable error

