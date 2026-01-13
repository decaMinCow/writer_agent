# story-linter Specification

## Purpose
TBD - created by archiving change add-knowledge-graph-and-story-linter. Update Purpose after archive.
## Requirements
### Requirement: Produce lint issues for story consistency
The system SHALL be able to compute consistency lint issues (hard/soft) for a given brief snapshot.

#### Scenario: Run linter and return issues
- **WHEN** the user runs the story linter for a snapshot
- **THEN** the system SHALL return a list of issues with severity, message, and references to relevant artifacts (when available)

