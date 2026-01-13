# novel-generation Specification

## Purpose
TBD - created by archiving change add-generation-workflows. Update Purpose after archive.
## Requirements
### Requirement: Generate a novel via ordered steps
The system SHALL generate novel outputs from a brief snapshot using ordered steps (plan → write → critique → fix → commit).

#### Scenario: Generate and commit a chapter
- **WHEN** the workflow generates a novel chapter draft for a specific chapter index
- **THEN** the system SHALL persist the chapter as a versioned artifact
- **AND** the system SHALL persist dual digests for the chapter (fact digest and tone digest)

### Requirement: Update CurrentState after commits
The system SHALL update `CurrentState` after each committed chapter based on the chapter’s factual events.

#### Scenario: CurrentState updated after chapter commit
- **WHEN** a chapter is committed
- **THEN** the workflow run state SHALL be updated with CurrentState changes (time/place/presence/inventory/known facts)

