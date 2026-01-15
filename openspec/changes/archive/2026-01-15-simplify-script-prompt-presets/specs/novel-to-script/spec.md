## MODIFIED Requirements

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
