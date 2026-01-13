# novel-to-script Specification

## Purpose
TBD - created by archiving change add-novel-to-script-workflow. Update Purpose after archive.
## Requirements
### Requirement: Convert committed novel chapters into committed script scenes
The system SHALL convert committed novel chapter artifacts into committed script scene artifacts using a stepwise workflow.

#### Scenario: Scene list derived from novel source
- **GIVEN** a brief snapshot has committed novel chapter versions
- **WHEN** a novel→script workflow run starts
- **THEN** the system SHALL generate and persist a structured `scene_list`

#### Scenario: Commit a scene with fidelity gating
- **WHEN** a scene is drafted and evaluated
- **THEN** the system SHALL block commit if hard fidelity constraints fail
- **AND** the system SHALL attempt targeted fixes before failing the run

### Requirement: Select source chapters from the same snapshot
The system SHALL use committed novel chapters associated with the same `brief_snapshot_id` as the workflow run.

#### Scenario: Missing novel sources fails with actionable error
- **GIVEN** no novel chapter versions exist for the snapshot
- **WHEN** the user runs a novel→script workflow
- **THEN** the system SHALL fail with an actionable error indicating novel sources are missing

### Requirement: Honor script format preference for novel→script
The system MUST format generated scenes according to `brief_snapshot.content.output_spec.script_format`.

#### Scenario: Script format applied in novel→script
- **WHEN** the workflow drafts a scene
- **THEN** the scene SHALL follow the configured script format preference

