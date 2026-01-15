# novel-to-script — Delta (add-global-novel-to-script-prompt)

## MODIFIED Requirements

### Requirement: Honor script format preference for novel→script
The system MUST format generated scenes according to `brief_snapshot.content.output_spec.script_format`, unless an explicit `conversion_output_spec` is configured for the run.

For `script_format_notes`, the system MUST apply the following precedence:
`conversion_output_spec.script_format_notes` > `brief_snapshot.content.output_spec.script_format_notes` > global novel→script prompt defaults.

#### Scenario: Script format applied in novel→script
- **WHEN** the workflow drafts a scene
- **THEN** the scene SHALL follow the configured script format preference

#### Scenario: Run-level conversion output spec overrides snapshot output spec
- **GIVEN** a novel→script workflow run is configured with a `conversion_output_spec`
- **WHEN** the workflow drafts a scene
- **THEN** the scene SHALL follow `conversion_output_spec.script_format` and related notes

#### Scenario: Global prompt applies when run notes and snapshot notes are missing
- **GIVEN** global novel→script prompt defaults are configured
- **AND** a novel→script workflow run does not provide `conversion_output_spec.script_format_notes`
- **AND** the selected snapshot/brief does not provide `output_spec.script_format_notes` (or the value is empty)
- **WHEN** the workflow drafts a scene or plans the scene list
- **THEN** the workflow SHALL use the global prompt defaults as conversion notes
