## ADDED Requirements

### Requirement: Right pane groups content into Project / Assets / Settings
The UI SHALL provide a clear separation of right-pane content into three groups so that project management, story assets, and global settings are not mixed in a single long scroll.

#### Scenario: Switch right pane tabs
- **GIVEN** the user is using the IDE UI
- **WHEN** the user selects a right-pane tab (Project / Assets / Settings)
- **THEN** the UI SHALL show only the panels relevant to that group
- **AND** the UI SHOULD remember the last selected tab locally for the next visit

### Requirement: UI uses Chinese labels for user-facing workflow and asset terms
The UI SHALL present user-facing labels in Chinese for common workflow and asset concepts.

#### Scenario: Translate workflow labels and statuses
- **WHEN** the UI renders workflow runs, steps, and controls
- **THEN** the UI SHALL display Chinese labels for names and statuses (while preserving internal enum values)

#### Scenario: Translate common configuration field labels
- **WHEN** the UI renders provider and preference settings
- **THEN** labels such as `Base URL`, `Chat Model`, `Embeddings Model`, `Timeout`, `Max Retries`, and `default` SHALL be displayed as clear Chinese equivalents

### Requirement: UI provides contextual help text for advanced panels
The UI SHALL provide short, grey helper text (and/or an expand/collapse help block) for panels that require user knowledge, so the user can understand what the feature does and how to use it.

#### Scenario: Open Threads panel explains usage with an example
- **GIVEN** the user opens the Open Threads (伏笔/线索) panel
- **THEN** the UI SHALL explain what a thread is, how to create one, and how to add references
- **AND** the UI SHALL explain the meaning of `introduced/reinforced/resolved` with a short example workflow

#### Scenario: KG/Lint panel explains when to run and how to jump
- **GIVEN** the user opens the KG/Lint panel
- **THEN** the UI SHALL explain the difference between “重建/运行” actions and the expected result
- **AND** the UI SHALL explain that clicking an issue can jump to the referenced artifact version (when available)
