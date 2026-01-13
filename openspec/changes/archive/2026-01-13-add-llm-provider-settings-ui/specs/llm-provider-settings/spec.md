# llm-provider-settings Specification (Delta)

## ADDED Requirements
### Requirement: Persist provider settings
The system SHALL persist a single-user, OpenAI-compatible provider configuration that can be used by LLM-backed features.

#### Scenario: Patch and read provider settings
- **WHEN** the user updates provider settings (base URL, models, timeout)
- **THEN** the system SHALL persist the settings and return the updated safe fields

### Requirement: API key is write-only
The system SHALL accept updates to the provider API key but SHALL NOT expose the API key value via any read API.

#### Scenario: Key is never returned
- **WHEN** the client requests provider settings
- **THEN** the response SHALL NOT include the API key
- **AND** the response SHALL include `api_key_configured: true|false`

#### Scenario: Clear stored key
- **WHEN** the client updates provider settings with `api_key: null`
- **THEN** the system SHALL clear the stored key and report `api_key_configured: false`

### Requirement: Provider settings enable LLM-backed endpoints
The system SHALL consider provider settings when determining whether LLM-backed endpoints/workflows are available.

#### Scenario: LLM-backed endpoint availability
- **GIVEN** a provider API key is configured via provider settings
- **WHEN** the user calls an endpoint that requires LLM access
- **THEN** the system SHALL proceed using the configured provider

### Requirement: Env fallback remains supported
The system SHALL continue to support env-based configuration as a fallback when provider settings are not configured.

#### Scenario: Run with env-only configuration
- **GIVEN** provider settings are not configured in the database
- **AND** `OPENAI_API_KEY` is configured via environment variables
- **WHEN** the user calls an endpoint that requires LLM access
- **THEN** the system SHALL proceed using the env configuration
