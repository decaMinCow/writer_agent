## ADDED Requirements

### Requirement: Hard checks gate commits
The system SHALL perform hard consistency checks before committing a chapter/scene and block commits that violate constraints.

#### Scenario: Commit is blocked by hard check failure
- **WHEN** a generated draft violates a hard constraint (e.g., dead character appears)
- **THEN** the system SHALL block commit and record an actionable error payload

### Requirement: Soft checks score quality and guide rewrites
The system SHALL run soft checks to score quality and guide targeted rewrites without rewriting unaffected sections.

#### Scenario: Targeted rewrite triggered by low rubric score
- **WHEN** a draft scores below a configured threshold in a rubric category
- **THEN** the system SHALL request a targeted rewrite for the failing section(s)
