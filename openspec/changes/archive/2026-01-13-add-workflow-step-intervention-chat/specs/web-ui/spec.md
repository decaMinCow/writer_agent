## ADDED Requirements

### Requirement: UI supports workflow node intervention chat
The web UI SHALL provide a “节点对话干预” panel when a workflow run is selected, allowing the user to send an instruction and apply the resulting state patch.

#### Scenario: Send an intervention from the UI
- **GIVEN** a workflow run is selected in the UI
- **WHEN** the user sends an intervention instruction
- **THEN** the UI SHALL call the intervention API
- **AND** the UI SHALL refresh run state and step history

