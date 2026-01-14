# web-ui — Delta (add-autorun-step-auto-retries)

## MODIFIED Requirements

### Requirement: UI supports brief/snapshot creation and preference editing
The web UI SHALL allow the user to create Briefs and Snapshots and to edit preferences without using the raw API.

#### Scenario: Edit global defaults and per-brief overrides
- **WHEN** the user edits global defaults and then clears per-brief overrides
- **THEN** the effective preferences shown in the UI SHALL reflect global defaults
- **AND** the UI SHALL allow editing `auto_step_retries` and `auto_step_backoff_s` as part of preferences

