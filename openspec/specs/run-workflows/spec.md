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

### Requirement: Delete a workflow run and its produced content
The system SHALL allow deleting a workflow run and SHALL delete the run history (step runs) and any content produced by that run (including artifact versions and dependent records).

#### Scenario: Delete a workflow run removes its step history and versions
- **GIVEN** a workflow run exists
- **AND** the run has one or more step runs
- **AND** the run produced one or more artifact versions
- **WHEN** the user deletes the workflow run
- **THEN** the system SHALL delete the workflow run
- **AND** the system SHALL delete its step runs
- **AND** the system SHALL delete artifact versions produced by the run
- **AND** the system SHALL delete any records that reference those deleted versions (e.g., memory chunks, KG events, lint issues, open thread refs, propagation events/impacts)

### Requirement: Apply chat-based interventions to workflow run state
The system SHALL allow applying a natural-language intervention to a workflow run, producing a state patch that updates `workflow_runs.state` and is persisted for audit.

#### Scenario: Apply an intervention tied to a selected step
- **GIVEN** a workflow run exists with one or more step runs
- **WHEN** the user submits an intervention instruction referencing a chosen step
- **THEN** the system SHALL generate an assistant response and a `state_patch`
- **AND** the system SHALL apply the patch to the workflow run state
- **AND** the system SHALL record the intervention as a `workflow_step_runs` entry

### Requirement: Configure novel→script run inputs at creation time
The system SHALL allow providing a source snapshot, a prompt preset, and a split mode when creating a `novel_to_script` workflow run.

#### Scenario: Create a novel→script run with a different source snapshot
- **GIVEN** two Snapshots exist for the same Brief
- **AND** the source snapshot has committed novel chapters
- **WHEN** the user creates a `novel_to_script` workflow run with `source_brief_snapshot_id` set to the source snapshot
- **THEN** the system SHALL create the run linked to the chosen `brief_snapshot_id`
- **AND** the system SHALL persist the source snapshot id in the run state for execution

#### Scenario: Create a novel→script run with a prompt preset
- **WHEN** the user creates a `novel_to_script` workflow run with `prompt_preset_id`
- **THEN** the system SHALL persist the chosen preset id in the workflow run state for later execution

#### Scenario: Create a novel→script run with a split mode
- **WHEN** the user creates a `novel_to_script` workflow run with `split_mode`
- **THEN** the system SHALL persist the chosen split mode in the workflow run state for later execution

#### Scenario: Missing split mode falls back to chapter-unit behavior
- **GIVEN** a novel→script workflow run is created without `split_mode`
- **WHEN** the workflow executes
- **THEN** the system SHALL behave as `1章=1集` by default

#### Scenario: Reject a source snapshot from another brief
- **GIVEN** a source snapshot exists but belongs to a different Brief than the run snapshot
- **WHEN** the user creates a `novel_to_script` run referencing that source snapshot
- **THEN** the system SHALL reject the request with an actionable error

### Requirement: Configure script run prompt preset at creation time
The system SHALL allow selecting a global prompt preset when creating a `script` workflow run.

#### Scenario: Create a script run with a prompt preset
- **WHEN** the user creates a `script` workflow run with `prompt_preset_id`
- **THEN** the system SHALL persist the chosen preset id in the workflow run state for later execution

