# novel-to-script — Delta (update-novel-to-script-episode-workflow)

## MODIFIED Requirements

### Requirement: Convert committed novel chapters into committed script scenes
The system SHALL convert committed novel chapter artifacts into committed script scene artifacts using a stepwise workflow.

#### Scenario: Episode-based conversion (1 chapter = 1 episode)
- **GIVEN** a brief snapshot has committed novel chapter versions
- **WHEN** a novel→script workflow run starts (default behavior for new runs)
- **THEN** the system SHALL process chapters in order and generate **one committed script artifact per chapter**
- **AND** the output for each chapter SHALL be a **complete episode unit** that may contain multiple scene blocks

#### Scenario: Episode workflow includes STEP1 breakdown and STEP2 script draft
- **WHEN** the workflow converts a chapter
- **THEN** the system SHALL first generate and persist a structured breakdown of core plot/conflicts (STEP1)
- **AND** the system SHALL then draft the episode script (STEP2) using the breakdown + chapter evidence + current state

#### Scenario: Episode output uses fixed numbering format for custom short-drama scripts
- **GIVEN** `output_spec.script_format` is `custom`
- **WHEN** the workflow drafts an episode
- **THEN** the episode text SHALL include exactly one `第X集` header
- **AND** scene blocks inside the episode SHALL be numbered `X.Y` (e.g. `11.1`, `11.2`), monotonic and non-duplicated
- **AND** the system SHALL block commit if the output violates these format constraints

#### Scenario: Commit an episode with fidelity gating
- **WHEN** an episode is drafted and evaluated
- **THEN** the system SHALL block commit if hard fidelity or format constraints fail
- **AND** the system SHALL attempt targeted fixes before failing the run

### Requirement: Honor script format preference for novel→script
The system MUST format generated scenes according to `brief_snapshot.content.output_spec.script_format`, unless an explicit `conversion_output_spec` is configured for the run.

For `script_format_notes`, the system MUST apply the following precedence:
`conversion_output_spec.script_format_notes` > `brief_snapshot.content.output_spec.script_format_notes` > global novel→script prompt defaults.

#### Scenario: Script format applied in novel→script
- **WHEN** the workflow drafts an episode/script unit
- **THEN** the output SHALL follow the configured script format preference

#### Scenario: Run-level conversion output spec overrides snapshot output spec
- **GIVEN** a novel→script workflow run is configured with a `conversion_output_spec`
- **WHEN** the workflow drafts an episode/script unit
- **THEN** the output SHALL follow `conversion_output_spec.script_format` and related notes
