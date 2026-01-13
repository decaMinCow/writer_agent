## ADDED Requirements

### Requirement: Gap report after each brief update
The system SHALL produce a gap report after each conversational update to a brief.

The gap report MUST classify brief fields into:
- `confirmed`: agreed and stable
- `pending`: suggested but not confirmed by the user
- `missing`: required for the selected workflow but not provided
- `conflict`: contradictory values detected

#### Scenario: User sends a message and receives a gap report
- **WHEN** the user sends a message to update a brief
- **THEN** the response SHALL include a gap report with `confirmed`, `pending`, `missing`, and `conflict` sections
- **AND** the response SHALL include follow-up questions that prioritize `conflict` then `missing`

### Requirement: Completeness score
The system SHALL compute a completeness score for the brief based on required fields for the selected workflow mode (novel/script/convert).

#### Scenario: Completeness score updates after edits
- **WHEN** the user updates the brief
- **THEN** the completeness score SHALL update to reflect the new state of required fields

