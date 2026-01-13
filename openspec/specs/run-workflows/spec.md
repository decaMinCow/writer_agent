# run-workflows Specification

## Purpose
TBD - created by archiving change add-foundation-mvp. Update Purpose after archive.
## Requirements
### Requirement: Create and track workflow runs
The system SHALL support workflow runs to track progress for novel generation, script generation, and novel-to-script conversion.

#### Scenario: Start a workflow run from a brief snapshot
- **WHEN** the user starts a workflow run and selects a brief snapshot
- **THEN** the system SHALL create a workflow run record linked to that snapshot
- **AND** the workflow run SHALL have a status (e.g., queued/running/paused/succeeded/failed/canceled)

#### Scenario: Pause and resume a workflow run
- **WHEN** the user pauses a running workflow
- **THEN** the system SHALL record the paused status and persist sufficient state to resume
- **WHEN** the user resumes a paused workflow
- **THEN** the system SHALL continue the workflow from the last completed step

### Requirement: Track workflow step runs
The system SHALL track per-step execution for a workflow run, including outputs and errors.

#### Scenario: Record step outputs
- **WHEN** a workflow step completes
- **THEN** the system SHALL persist step status and outputs (including references to produced artifacts)

#### Scenario: Record step failures
- **WHEN** a workflow step fails
- **THEN** the system SHALL persist the failure status and error details for debugging

