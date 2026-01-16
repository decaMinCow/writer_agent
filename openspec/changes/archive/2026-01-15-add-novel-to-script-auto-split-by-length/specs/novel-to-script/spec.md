## ADDED Requirements

### Requirement: Auto-split chapters into multiple script episodes by target length
When a `novel_to_script` workflow run is configured for auto-splitting, the system SHALL split a single novel chapter into multiple script episodes based on the target per-episode length implied by the selected prompt preset.

This mode SHALL:
- run STEP1 “核心剧情梳理/拆解” **once per chapter**
- generate **one or more** script episodes for that chapter (each episode may contain multiple scenes)
- NOT cross chapter boundaries when generating episodes

#### Scenario: Enable auto-splitting for a novel→script run
- **GIVEN** a novel→script workflow run exists with `split_mode=auto_by_length`
- **AND** committed novel chapters exist for the effective source snapshot
- **WHEN** the workflow converts a chapter
- **THEN** the system SHALL generate a chapter-level plan (STEP1) once
- **AND** the system SHALL draft and commit multiple script episodes for that chapter as needed
- **AND** each committed episode SHALL record which source chapter it came from (e.g., via metadata)

#### Scenario: Derive target length from prompt preset text
- **GIVEN** the selected novel→script prompt preset text includes a per-episode length range (e.g. `500-800字`)
- **WHEN** the workflow plans splitting for a chapter
- **THEN** the system SHALL use that range as the target episode length range for planning and checks
- **AND** if no range can be derived, the system SHALL fall back to a safe default range

#### Scenario: Count episode length using “no whitespace + no punctuation”
- **WHEN** the workflow evaluates whether a drafted episode meets the target length range
- **THEN** the system SHALL compute length by removing whitespace and punctuation before counting characters

#### Scenario: Allow small overflow beyond the max range
- **GIVEN** an episode’s computed length exceeds the configured max length
- **WHEN** the overflow is within a small tolerance band
- **THEN** the system SHOULD allow commit (with a warning/soft signal)
- **AND** if the overflow exceeds the tolerance band, the system SHALL trigger the fix loop (or fail if fixes are exhausted)
