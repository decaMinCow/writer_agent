# global-settings — Delta (add-global-novel-to-script-prompt)

## ADDED Requirements

### Requirement: Global novel→script prompt defaults
The system SHALL persist and expose a global default prompt (text) used by the `novel_to_script` workflow when run-level conversion notes and snapshot-level notes are not provided.

#### Scenario: Get global novel→script prompt defaults
- **WHEN** the client requests the novel→script prompt defaults
- **THEN** the system SHALL return a JSON object that includes `conversion_notes` (nullable string)

#### Scenario: Update global novel→script prompt defaults
- **WHEN** the client updates the novel→script prompt defaults
- **THEN** the system SHALL persist the updated value and return the resolved value
