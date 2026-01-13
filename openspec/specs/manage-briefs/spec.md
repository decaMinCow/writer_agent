# manage-briefs Specification

## Purpose
TBD - created by archiving change add-foundation-mvp. Update Purpose after archive.
## Requirements
### Requirement: Create and update a Creative Brief
The system SHALL persist a Creative Brief as structured data and allow it to be created and updated.

#### Scenario: Create a brief
- **WHEN** the user creates a new brief
- **THEN** the system SHALL persist the brief and assign it a stable identifier

#### Scenario: Update a brief
- **WHEN** the user updates an existing brief
- **THEN** the system SHALL persist the updated brief contents
- **AND** the system SHALL preserve the brief identifier

### Requirement: Version a Creative Brief via snapshots
The system SHALL support immutable Brief Snapshots that represent a versioned point-in-time copy of a Creative Brief.

#### Scenario: Create a brief snapshot
- **WHEN** the user requests a snapshot of a brief
- **THEN** the system SHALL create an immutable snapshot record linked to the brief
- **AND** subsequent edits to the brief SHALL NOT change the snapshot

#### Scenario: List and retrieve brief snapshots
- **WHEN** the user lists snapshots for a brief
- **THEN** the system SHALL return the snapshots in reverse chronological order
- **AND** the user SHALL be able to retrieve any snapshot by identifier

### Requirement: Configure output specifications, including script format
The system SHALL store output specifications as part of the Creative Brief, including a configurable screenplay/script formatting preference.

#### Scenario: Update script formatting preference independently
- **WHEN** the user updates the script formatting preference in the brief output specification
- **THEN** the system SHALL persist the change without requiring unrelated brief fields to be modified
- **AND** newly started workflow runs SHALL reference a snapshot that includes the updated preference

