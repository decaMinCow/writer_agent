## ADDED Requirements

### Requirement: Forking preserves stepwise execution
Forked runs SHALL remain compatible with stepwise execution.

#### Scenario: Execute next step after forking
- **WHEN** a forked run executes the next step
- **THEN** the system SHALL continue from the forked state cursor without affecting the source run

