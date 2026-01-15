## ADDED Requirements

### Requirement: Use prompt preset text for script generation style/format notes
The system SHALL apply the selected global `script` prompt preset when generating scripts so the user can control style/format via editable text templates.

#### Scenario: Script run uses a selected preset
- **GIVEN** a `script` workflow run is configured with `state.prompt_preset_id`
- **WHEN** the workflow drafts a script scene
- **THEN** the workflow SHALL resolve the preset id within the global `script` preset catalog
- **AND** the workflow SHALL inject the preset text as `output_spec.script_format_notes` for prompting

#### Scenario: Script run falls back to the global default preset
- **GIVEN** a `script` workflow run has no `state.prompt_preset_id`
- **WHEN** the workflow drafts a script scene
- **THEN** the workflow SHALL inject the global default `script` preset text as `output_spec.script_format_notes`
