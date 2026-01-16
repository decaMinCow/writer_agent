## MODIFIED Requirements
### Requirement: Global output preferences
The system SHALL persist and expose global default output preferences for the single-user app, and apply those defaults to snapshots and workflows.

#### Scenario: Get global defaults
- **WHEN** the client requests global output preferences
- **THEN** the system SHALL return a JSON object with default `output_spec` fields
- **AND** the defaults SHALL include `auto_step_retries` and `auto_step_backoff_s`

#### Scenario: Update global defaults
- **WHEN** the client updates global output preferences
- **THEN** the system SHALL persist the new defaults and return the updated values

#### Scenario: Apply global defaults to snapshots
- **WHEN** global defaults are updated
- **THEN** newly created snapshots SHALL use those defaults for preference fields in `output_spec`
