# novel-to-script — Delta (add-novel-to-script-conversion-config)

## MODIFIED Requirements

### Requirement: Select source chapters from the same snapshot
The system SHALL use committed novel chapters associated with the same `brief_snapshot_id` as the workflow run, unless an explicit source snapshot is provided for the run.

#### Scenario: Default source uses the run snapshot
- **GIVEN** a novel→script workflow run exists
- **AND** no explicit source snapshot is configured for the run
- **WHEN** the workflow selects novel chapter sources
- **THEN** the system SHALL use committed novel chapters associated with the run's `brief_snapshot_id`

#### Scenario: Source snapshot override uses the configured source snapshot
- **GIVEN** a novel→script workflow run exists
- **AND** the run is configured with a `source_brief_snapshot_id`
- **WHEN** the workflow selects novel chapter sources
- **THEN** the system SHALL use committed novel chapters associated with `source_brief_snapshot_id`

#### Scenario: Missing novel sources fails with actionable error
- **GIVEN** no novel chapter versions exist for the effective source snapshot
- **WHEN** the user runs a novel→script workflow
- **THEN** the system SHALL fail with an actionable error indicating novel sources are missing

### Requirement: Honor script format preference for novel→script
The system MUST format generated scenes according to `brief_snapshot.content.output_spec.script_format`, unless an explicit `conversion_output_spec` is configured for the run.

#### Scenario: Script format applied in novel→script
- **WHEN** the workflow drafts a scene
- **THEN** the scene SHALL follow the configured script format preference

#### Scenario: Run-level conversion output spec overrides snapshot output spec
- **GIVEN** a novel→script workflow run is configured with a `conversion_output_spec`
- **WHEN** the workflow drafts a scene
- **THEN** the scene SHALL follow `conversion_output_spec.script_format` and related notes

