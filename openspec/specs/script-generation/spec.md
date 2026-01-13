# script-generation Specification

## Purpose
TBD - created by archiving change add-generation-workflows. Update Purpose after archive.
## Requirements
### Requirement: Generate a script via ordered steps
The system SHALL generate screenplay/script outputs from a brief snapshot using ordered steps (plan → write → critique → fix → commit).

#### Scenario: Generate and commit a scene
- **WHEN** the workflow generates a script scene
- **THEN** the system SHALL persist the scene as a versioned artifact
- **AND** the scene SHALL be formatted according to the brief output specification

### Requirement: Honor script format preference
The system MUST format script outputs according to `brief.output_spec.script_format`.

#### Scenario: Script format is applied
- **WHEN** the brief specifies a script format preference
- **THEN** generated scenes SHALL follow that formatting preference

