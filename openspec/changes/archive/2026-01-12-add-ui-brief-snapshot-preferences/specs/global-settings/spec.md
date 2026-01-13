## ADDED Requirements

### Requirement: Global output preferences
The system SHALL persist and expose global default output preferences for the single-user app.

#### Scenario: Get global defaults
- **WHEN** the client requests global output preferences
- **THEN** the system SHALL return a JSON object with default `output_spec` fields

#### Scenario: Update global defaults
- **WHEN** the client updates global output preferences
- **THEN** the system SHALL persist the new defaults and return the updated values

