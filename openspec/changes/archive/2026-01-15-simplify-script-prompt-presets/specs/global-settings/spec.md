## ADDED Requirements

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
