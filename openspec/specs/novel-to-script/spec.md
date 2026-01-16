# novel-to-script Specification

## Purpose
TBD - created by archiving change add-novel-to-script-workflow. Update Purpose after archive.
## Requirements
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
- **THEN** the episode text SHALL include exactly one episode header (e.g. `第1集` or `第一集`) that matches the episode index
- **AND** scene blocks inside the episode SHALL be numbered `X-Y` (default, e.g. `11-1`, `11-2`) or `X.Y` (accepted), monotonic and non-duplicated
- **AND** the system SHALL block commit if the output violates these format constraints

#### Scenario: Commit an episode with fidelity gating
- **WHEN** an episode is drafted and evaluated
- **THEN** the system SHALL block commit if hard fidelity or format constraints fail
- **AND** the system SHALL attempt targeted fixes before failing the run

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
The system MUST format novel→script outputs using a resolved output specification and prompt preset rules.

For `script_format_notes`, the system MUST apply the following precedence:
`workflow_runs.state.prompt_preset_id` (resolved to preset text) > global default novel→script preset text.

The system MUST NOT use Snapshot/Brief `output_spec.script_format_notes` as novel→script conversion rules.

#### Scenario: Script format applied in novel→script
- **WHEN** the workflow drafts an episode/script unit
- **THEN** the output SHALL follow the resolved script format preference

#### Scenario: Run-level prompt preset overrides the global default
- **GIVEN** a novel→script workflow run is configured with `state.prompt_preset_id`
- **WHEN** the workflow drafts an episode/script unit
- **THEN** the workflow SHALL resolve the preset id within the global novel→script preset catalog
- **AND** the workflow SHALL use the resolved preset text as `output_spec.script_format_notes`

#### Scenario: Missing preset id falls back to global default
- **GIVEN** a novel→script workflow run has no `state.prompt_preset_id`
- **WHEN** the workflow drafts an episode/script unit
- **THEN** the workflow SHALL use the global default novel→script preset text as `output_spec.script_format_notes`

### Requirement: Auto-split chapters into multiple script episodes by target length
When a `novel_to_script` workflow run is configured for auto-splitting, the system SHALL split a single novel chapter into multiple script episodes based on the target per-episode length implied by the selected prompt preset.

This mode SHALL:
- run STEP1 “核心剧情梳理/拆解” **once per chapter**
- generate **one or more** script episodes for that chapter (each episode may contain multiple scenes)
- NOT cross chapter boundaries when generating episodes

#### Scenario: Enable auto-splitting for a novel→script run
- **GIVEN** a novel→script workflow run exists with `split_mode=auto_by_length`
- **AND** committed novel chapters exist for the effective source snapshot
- **WHEN** the workflow converts a chapter
- **THEN** the system SHALL generate a chapter-level plan (STEP1) once
- **AND** the system SHALL draft and commit multiple script episodes for that chapter as needed
- **AND** each committed episode SHALL record which source chapter it came from (e.g., via metadata)

#### Scenario: Derive target length from prompt preset text
- **GIVEN** the selected novel→script prompt preset text includes a per-episode length range (e.g. `500-800字`)
- **WHEN** the workflow plans splitting for a chapter
- **THEN** the system SHALL use that range as the target episode length range for planning and checks
- **AND** if no range can be derived, the system SHALL fall back to a safe default range

#### Scenario: Count episode length using “no whitespace + no punctuation”
- **WHEN** the workflow evaluates whether a drafted episode meets the target length range
- **THEN** the system SHALL compute length by removing whitespace and punctuation before counting characters

#### Scenario: Allow small overflow beyond the max range
- **GIVEN** an episode’s computed length exceeds the configured max length
- **WHEN** the overflow is within a small tolerance band
- **THEN** the system SHOULD allow commit (with a warning/soft signal)
- **AND** if the overflow exceeds the tolerance band, the system SHALL trigger the fix loop (or fail if fixes are exhausted)

