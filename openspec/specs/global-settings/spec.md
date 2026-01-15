# global-settings Specification

## Purpose
TBD - created by archiving change add-ui-brief-snapshot-preferences. Update Purpose after archive.
## Requirements
### Requirement: Global output preferences
The system SHALL persist and expose global default output preferences for the single-user app.

#### Scenario: Get global defaults
- **WHEN** the client requests global output preferences
- **THEN** the system SHALL return a JSON object with default `output_spec` fields
- **AND** the defaults SHALL include `auto_step_retries` and `auto_step_backoff_s`

#### Scenario: Update global defaults
- **WHEN** the client updates global output preferences
- **THEN** the system SHALL persist the new defaults and return the updated values

### Requirement: Global novel→script prompt defaults
The system SHALL persist and expose a global default prompt (text) used by the `novel_to_script` workflow when run-level conversion notes and snapshot-level notes are not provided.

#### Scenario: Get global novel→script prompt defaults
- **WHEN** the client requests the novel→script prompt defaults
- **THEN** the system SHALL return a JSON object that includes `conversion_notes` (nullable string)

#### Scenario: Update global novel→script prompt defaults
- **WHEN** the client updates the novel→script prompt defaults
- **THEN** the system SHALL persist the updated value and return the resolved value

### Requirement: Global prompt preset catalogs for script and novel→script
The system SHALL persist and expose global prompt preset catalogs for (1) direct script generation and (2) novel→script conversion.

Each catalog SHALL support multiple presets and a default preset selection.

#### Scenario: Get prompt preset catalogs
- **WHEN** the client requests global prompt preset catalogs
- **THEN** the system SHALL return JSON that includes:
  - a `script` catalog (presets + default id)
  - a `novel_to_script` catalog (presets + default id)

#### Scenario: Update prompt preset catalogs
- **WHEN** the client updates the prompt preset catalogs
- **THEN** the system SHALL persist the updated catalogs
- **AND** the system SHALL validate that the default preset id (if provided) exists in the corresponding catalog (or fall back safely)

