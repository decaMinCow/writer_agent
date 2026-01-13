# propagation-engine Specification

## Purpose
TBD - created by archiving change add-propagation-engine. Update Purpose after archive.
## Requirements
### Requirement: Preview change propagation from an edited artifact
The system SHALL support previewing the factual changes introduced by an edited artifact version.

#### Scenario: Preview fact diffs
- **GIVEN** a base artifact version and an edited artifact version
- **WHEN** the user requests a propagation preview
- **THEN** the system SHALL return a structured summary of fact changes and a list of impacted artifacts (if any)

### Requirement: Mark impacted artifacts and support repair
The system SHALL persist propagation events, mark impacted artifacts, and allow generating repaired versions.

#### Scenario: Apply propagation and repair
- **WHEN** the user applies a propagation event
- **THEN** the system SHALL mark impacted artifacts as needing repair
- **AND** the user SHALL be able to trigger repair to create new artifact versions

