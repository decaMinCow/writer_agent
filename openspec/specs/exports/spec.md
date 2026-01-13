# exports Specification

## Purpose
TBD - created by archiving change add-export-and-formatting-tools. Update Purpose after archive.
## Requirements
### Requirement: Export compiled novel text per snapshot
The system SHALL support exporting a compiled novel from the latest chapter versions for a given snapshot.

#### Scenario: Export novel as Markdown
- **GIVEN** a snapshot has one or more committed novel chapters
- **WHEN** the user exports the novel
- **THEN** the system SHALL return a Markdown document ordered by chapter ordinal

### Requirement: Export compiled script per snapshot
The system SHALL support exporting a compiled script from the latest scene versions for a given snapshot.

#### Scenario: Export script as Fountain
- **GIVEN** a snapshot has one or more committed script scenes
- **WHEN** the user exports the script
- **THEN** the system SHALL return a Fountain document ordered by scene ordinal

### Requirement: Apply terminology replacements during export
The system SHALL allow applying snapshot-scoped terminology replacements during export.

#### Scenario: Export with replacements
- **GIVEN** the user has defined terminology replacements for a snapshot
- **WHEN** the user exports the novel/script with replacements enabled
- **THEN** the exported output SHALL reflect the replacements without mutating stored artifacts

