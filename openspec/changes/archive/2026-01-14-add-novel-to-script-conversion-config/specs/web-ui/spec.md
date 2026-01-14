# web-ui — Delta (add-novel-to-script-conversion-config)

## MODIFIED Requirements

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

