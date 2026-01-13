# open-threads Specification

## Purpose
TBD - created by archiving change add-open-threads-management. Update Purpose after archive.
## Requirements
### Requirement: Manage open threads per brief snapshot
The system SHALL support Open Threads (foreshadowing items) scoped by `brief_snapshot_id`.

#### Scenario: Create and close a thread
- **WHEN** the user creates an open thread and later marks it resolved
- **THEN** the system SHALL persist its status and description and retain history

### Requirement: Link threads to artifact versions
The system SHALL allow open threads to be referenced by artifact versions (introduced/reinforced/resolved).

#### Scenario: Reference a thread from a chapter/scene
- **GIVEN** an artifact version exists
- **WHEN** the user links it as a thread reference
- **THEN** the system SHALL persist the link and allow navigation from the thread to the artifact version

