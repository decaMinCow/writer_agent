## MODIFIED Requirements
### Requirement: UI supports brief/snapshot creation and preference editing
The web UI SHALL allow the user to create Briefs and Snapshots and to edit global preferences without using the raw API.

#### Scenario: Edit global defaults only
- **WHEN** the user edits global defaults
- **THEN** the UI SHALL show only global defaults and SHALL NOT present per-brief override controls
- **AND** the UI SHALL allow editing `auto_step_retries` and `auto_step_backoff_s` as part of global preferences
