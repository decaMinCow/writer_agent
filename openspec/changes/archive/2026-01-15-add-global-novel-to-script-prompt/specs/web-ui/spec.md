# web-ui — Delta (add-global-novel-to-script-prompt)

## ADDED Requirements

### Requirement: UI can configure global novel→script prompt defaults
The web UI SHALL provide an editor for the global novel→script prompt defaults.

#### Scenario: Edit global novel→script prompt defaults
- **WHEN** the user edits and saves the global novel→script prompt defaults in the UI
- **THEN** the UI SHALL persist the value via the settings API

## MODIFIED Requirements

### Requirement: UI can create novel→script runs
The web UI SHALL allow the user to create and run `novel_to_script` workflow runs from a selected brief snapshot, and SHALL allow configuring source snapshot and conversion rules at run creation time.

#### Scenario: Create a novel→script run
- **WHEN** the user selects a snapshot and chooses “小说→剧本”
- **THEN** the UI SHALL create a workflow run and allow stepwise execution

#### Scenario: Leave conversion notes blank to use lower-precedence notes
- **GIVEN** the user selects “小说→剧本”
- **WHEN** the user leaves conversion notes blank
- **THEN** the created run SHALL omit run-level notes so the backend can apply snapshot/brief notes (or global defaults if snapshot notes are missing)
