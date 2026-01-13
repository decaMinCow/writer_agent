# web-ui Specification (Delta)

## ADDED Requirements
### Requirement: UI can configure model provider settings
The web UI SHALL provide a panel to view and update the OpenAI-compatible provider settings used by the backend.

#### Scenario: Save provider settings in the UI
- **WHEN** the user enters a base URL and API key and clicks save
- **THEN** the UI SHALL persist the settings via the API and indicate that an API key is configured

#### Scenario: Clear provider API key in the UI
- **WHEN** the user clears the stored key
- **THEN** the UI SHALL show the provider as unconfigured and report errors from LLM-backed features

